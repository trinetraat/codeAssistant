# CodeAssistant CLI – Quick Usage Guide

CodeAssistant is a local developer agent for generating, fixing, and tracking code deliverables with OpenAI (or Azure OpenAI).  
This guide summarizes the most common commands and workflow.

---

## 📂 Project Lifecycle

### 1. Initialize a project
Creates a session file and spec stub for persistent context + billing.

```bash
codeassistant init <project_id>
```

Example:
```bash
codeassistant init loan-parquet-test
```

---

### 2. Generate code
Main workhorse: generate a full runnable script.

```bash
codeassistant gen <project_id>   --lang py   --mode fabric   --model gpt-4.1-mini   --paths "/path/to/schema.json" "/path/to/loan.json"   --requirement "Normalize loan.json to tables per schema, propagate loanId, save Parquet (Fabric/Synapse compatible)."
```

- **`--lang`**: `py`, `pyspark`, or `sql`  
- **`--mode`**: `code`, `fabric`, `azure-func`, `pipeline`, `api`, `deploy`  
- **`--model`**: optional (otherwise uses default or last chosen)  
- **`--paths`**: optional file(s)/folder(s) to include as hints  
- **`--requirement`**: short description of the deliverable  

The generated script is saved under:

```
~/.codeassistant/outputs/<project_id>_YYYYMMDD_HHMMSS.py
```

---

### 3. Run your code
Execute the generated script in your own environment.

```bash
python ~/.codeassistant/outputs/<filename>.py --args...
```

If it fails, capture the traceback for the next step.

---

### 4. Fix errors
Feed error output back into the assistant.

```bash
# Save traceback
python <generated_script>.py ... 2>&1 | tee errors.txt

# Ask CodeAssistant to fix
codeassistant fix <project_id> --error-file errors.txt
```

The fixed version is saved as:

```
~/.codeassistant/outputs/<project_id>_fixed_YYYYMMDD_HHMMSS.py
```

---

### 5. Pin a spec (optional)
Attach organizational rules, naming conventions, or SLAs to a project.  
This text is always included in future `gen` / `fix` runs.

```bash
codeassistant pin-spec <project_id> --file SPEC.md
```

---

### 6. Check costs
View cumulative spend per project.

```bash
codeassistant cost <project_id>
```

---

## 🔄 Typical Workflow

1. **Init once per project**  
   ```bash
   codeassistant init loan-parquet-test
   ```

2. **Generate code**  
   ```bash
   codeassistant gen loan-parquet-test --lang py --mode fabric --requirement "..."
   ```

3. **Run locally** → if it errors, save the traceback

4. **Fix it**  
   ```bash
   codeassistant fix loan-parquet-test --error-file errors.txt
   ```

5. **Repeat** until working  
6. **Check spend** anytime with  
   ```bash
   codeassistant cost loan-parquet-test
   ```

---

## 📂 Where things live

- **Sessions (history + billing):**  
  `~/.codeassistant/sessions/<project_id>.json`

- **Generated code:**  
  `~/.codeassistant/outputs/<project_id>_*.py`

- **Specs (pinned rules):**  
  `~/.codeassistant/specs/<project_id>.md`

---

## ✅ Tips
- Always keep your `.env` file with your `OPENAI_API_KEY` in the repo root.  
- Closing your terminal does **not** lose history — sessions are on disk.  
- Use `_fixed_*.py` files after `fix`, not the old broken ones.  
- To avoid confusion, consider copying the latest generated file into your repo’s `generated/` folder.

---
