import argparse, os, sys, datetime
from pathlib import Path
from codeassistant.core.config import PRICING, DEFAULT_MODEL, get_api_env
from codeassistant.core.session import load_session, save_session, add_turn, outputs_dir, spec_path
import codeassistant.core.prompts as ca_prompts
from codeassistant.core.cost import estimate_cost_usd
from codeassistant.core.oa_client import make_client_or_die

def _coerce_usage(usage):
    if not usage:
        return {}
    try:
        inp = int(getattr(usage, "input_tokens", 0) or 0)
        outp = int(getattr(usage, "output_tokens", 0) or 0)
        return {"input_tokens": inp, "output_tokens": outp, "total_tokens": inp + outp}
    except Exception:
        return {}

def _resolve_requirement_arg(val: str | None) -> str | None:
    if not val:
        # auto-default: ./requirements_brief.txt if present
        p = Path.cwd()/ "requirements_brief.txt"
        return p.read_text(encoding="utf-8") if p.exists() else None
    if val == "-":  # read from stdin
        return sys.stdin.read()
    if val.startswith("@"):  # read from file
        p = Path(val[1:]).expanduser().resolve()
        return p.read_text(encoding="utf-8")
    return val

def pick_model_interactive(current: str) -> str:
    print(f"\nModel (current={current or DEFAULT_MODEL}):")
    keys = list(PRICING.keys())
    for i, k in enumerate(keys, 1):
        p = PRICING[k]
        print(f"  {i}. {k}  (${p['input']}/M in, ${p['output']}/M out)")
    raw = input("Choose [ENTER keep]: ").strip()
    if not raw: return current or DEFAULT_MODEL
    if raw.isdigit() and 1 <= int(raw) <= len(keys): return keys[int(raw)-1]
    if raw in PRICING: return raw
    print("Keeping current."); return current or DEFAULT_MODEL

def read_head(p: Path, max_lines=60) -> str:
    if not p.exists(): return ""
    return "\n".join(p.read_text(encoding="utf-8", errors="ignore").splitlines()[:max_lines])

def main():
    parser = argparse.ArgumentParser(prog="codeassistant", description="Local code assistant CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_init = sub.add_parser("init", help="Initialize a project")
    p_init.add_argument("project_id")

    p_spec = sub.add_parser("pin-spec", help="Pin/update a project spec from a file")
    p_spec.add_argument("project_id")
    p_spec.add_argument("--file", required=True, help="Path to a markdown/txt spec")

    p_gen = sub.add_parser("gen", help="Generate code")
    p_gen.add_argument("project_id")
    p_gen.add_argument("--lang", default="py", choices=["py","pyspark","sql"])
    p_gen.add_argument("--mode", default="code", choices=["code","azure-func","pipeline","fabric","api","deploy"])
    p_gen.add_argument("--model", default=None)
    p_gen.add_argument("--requirement", default=None, help="If omitted, will prompt interactively")
    p_gen.add_argument("--paths", nargs="*", default=[], help="Optional paths to files/folders to reference")

    p_fix = sub.add_parser("fix", help="Paste errors to regenerate")
    p_fix.add_argument("project_id")
    p_fix.add_argument("--model", default=None)
    p_fix.add_argument("--error", default=None)
    p_fix.add_argument("--error-file", default=None)

    p_cost = sub.add_parser("cost", help="Show project running total")
    p_cost.add_argument("project_id")

    args = parser.parse_args()

    if args.cmd == "init":
        proj = load_session(args.project_id)
        if not proj.get("model"):
            proj["model"] = DEFAULT_MODEL
        save_session(proj)
        sp = spec_path(args.project_id)
        if not sp.exists(): sp.write_text("# Project spec\n\n(put org rules, naming, SLAs here)\n", encoding="utf-8")
        print(f"✅ Initialized {args.project_id}\nSessions: {sp.parent}\nSpec: {sp}")
        return

    if args.cmd == "pin-spec":
        src = Path(args.file)
        if not src.exists():
            print("❌ Spec file not found"); sys.exit(1)
        dst = spec_path(args.project_id)
        dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"✅ Spec pinned at {dst}")
        return

    if args.cmd == "cost":
        proj = load_session(args.project_id)
        total = proj.get("billing",{}).get("total_usd",0.0)
        print(f"💵 {args.project_id} total: ${total:.4f}")
        return

    # GEN / FIX need OpenAI env
    env = get_api_env()
    if not (env["OPENAI_API_KEY"] or (env["AZURE_OPENAI_API_KEY"] and env["AZURE_OPENAI_ENDPOINT"])):
        print("❌ Set OPENAI_API_KEY or (AZURE_OPENAI_API_KEY + AZURE_OPENAI_ENDPOINT).")
        sys.exit(1)
    client = make_client_or_die()

    proj = load_session(args.project_id)
    model = args.model or proj.get("model") or DEFAULT_MODEL

    if args.cmd == "gen":
        # allow interactive model change
        if args.model:
            # user explicitly set it -> take it, no prompt
            proj["model"] = args.model
            model = args.model
        else:
            # no explicit flag -> allow interactive change
            model = pick_model_interactive(model)
            proj["model"] = model

        args.requirement = _resolve_requirement_arg(args.requirement)
        requirement = args.requirement or input("Describe the deliverable: ").strip()
        # tiny “paths hint”: we just list paths; generated code reads them at runtime
        hint_paths = ""
        for p in (args.paths or []):
            hint_paths += str(Path(p).resolve()) + "\n"

        system_prompt = ca_prompts.build_system_prompt(args.mode)
        pinned_head = read_head(spec_path(args.project_id))
        brief = ca_prompts.build_user_brief(requirement, args.lang, pinned_head, hint_paths)

        messages = [{"role":"system","content": system_prompt}]
        # keep last few turns small
        for t in proj["turns"][-6:]:
            messages.append({"role": t["role"], "content": t["content"]})
        messages.append({"role":"user","content": brief})

        print(f"\n⏳ Generating with {model} …")
        try:
            resp = client.responses.create(model=model, input=messages)
        except Exception as e:
            print(f"❌ API error: {e}"); sys.exit(1)
        code = resp.output_text
        usage = getattr(resp, "usage", None)
        cost  = estimate_cost_usd(model, usage)

        add_turn(proj, "user", brief)
        add_turn(proj, "assistant", code, _coerce_usage(usage))

        proj["billing"]["total_usd"] = round(proj["billing"]["total_usd"] + cost, 6)
        proj["billing"]["turns"].append({
            "ts": datetime.datetime.utcnow().isoformat(),
            "model": model,
            "input_tokens": int(getattr(usage, "input_tokens", 0) or 0) if usage else 0,
            "output_tokens": int(getattr(usage, "output_tokens", 0) or 0) if usage else 0,
            "cost_usd": round(cost, 6),
        })
        save_session(proj)

        ext = {"py":"py","pyspark":"py","sql":"sql"}[args.lang]
        out = (outputs_dir() / f"{args.project_id}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.{ext}")
        out.write_text(code, encoding="utf-8")
        print(f"✅ Wrote: {out}")
        print(f"💵 Turn: ${cost:.4f} | Total: ${proj['billing']['total_usd']:.4f}")
        return

    if args.cmd == "fix":
        err_text = args.error or ""
        if args.error_file:
            p = Path(args.error_file); err_text += "\n" + p.read_text(encoding="utf-8")
        if not err_text.strip():
            print("Paste errors, end with CTRL+Z (Windows) or CTRL+D (Unix):")
            try:
                err_text = sys.stdin.read()
            except KeyboardInterrupt:
                print("Cancelled"); sys.exit(1)
        model = args.model or proj.get("model") or DEFAULT_MODEL
        system_prompt = ca_prompts.build_system_prompt("code")
        pinned_head = read_head(spec_path(args.project_id))
        brief = f"Errors to fix; return FULL corrected file.\n\n{err_text}\n\n(Pinned spec follows)\n{pinned_head}"

        messages = [{"role":"system","content": system_prompt}]
        for t in proj["turns"][-6:]:
            messages.append({"role": t["role"], "content": t["content"]})
        messages.append({"role":"user","content": brief})

        print(f"\n⏳ Fixing with {model} …")
        try:
            resp = client.responses.create(model=model, input=messages)
        except Exception as e:
            print(f"❌ API error: {e}"); sys.exit(1)
        code = resp.output_text
        usage = getattr(resp, "usage", None)
        cost  = estimate_cost_usd(model, usage)

        add_turn(proj, "user", brief)
        add_turn(proj, "assistant", code, _coerce_usage(usage))

        proj["billing"]["total_usd"] = round(proj["billing"]["total_usd"] + cost, 6)
        proj["billing"]["turns"].append({
            "ts": datetime.datetime.utcnow().isoformat(),
            "model": model,
            "input_tokens": int(getattr(usage, "input_tokens", 0) or 0) if usage else 0,
            "output_tokens": int(getattr(usage, "output_tokens", 0) or 0) if usage else 0,
            "cost_usd": round(cost, 6),
        })
        save_session(proj)

        out = (outputs_dir() / f"{args.project_id}_fixed_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.py")
        out.write_text(code, encoding="utf-8")
        print(f"🔧 Wrote: {out}")
        print(f"💵 Turn: ${cost:.4f} | Total: ${proj['billing']['total_usd']:.4f}")
        return