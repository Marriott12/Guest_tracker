Import command usage

This project provides a management command to import event program, menu, and seating JSON files:

Usage (local):

```powershell
& .venv/Scripts/Activate.ps1
python manage.py import_event_data --program program.json --menu menu.json --seating seating.json
```

Options:
- `--program` Path to a program JSON (default: `program.json` at project root)
- `--menu` Path to a menu JSON (default: `menu.json` at project root)
- `--seating` Path to a seating JSON (default: `seating.json` at project root)
- `--emails` Optional JSON mapping of guest full names to email addresses. Example content:

```json
{
  "Capt. John Smith": "john.smith@example.com",
  "Ms. Jane Doe": "jane.doe@example.com"
}
```

Notes:
- The command is idempotent: running it multiple times will update the existing event (matched by name+date) and create missing guests/invitations.
- The command will attempt to generate QR codes and 1D barcodes for invitations when missing.

CI: To run this command on-demand in CI, see `.github/workflows/import_event.yml` for an example `workflow_dispatch` job that invokes the command.
