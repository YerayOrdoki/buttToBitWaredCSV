# Buttercup to Bitwarden CSV converter

Convert a CSV export from Buttercup into a Bitwarden-compatible CSV. The script reconstructs Buttercup groups as Bitwarden folders, including nested groups.

**Security warning:** Both the input and output CSV files contain passwords in plain text. Run the converter locally. Never upload either CSV file to GitHub, share it, or store it in a public or untrusted location.

## Requirements

- Python 3; no third-party packages are required.
- A CSV exported from Buttercup Desktop.

## Configure the paths

Edit these lines near the top of `convertir_buttercup_bitwarden.py`:

```python
# Directory containing the Buttercup CSV file.
# The converted Bitwarden CSV file will also be saved here.
# Change "Escritorio" to another directory if needed.
base = Path.home() / "Escritorio"

# Name of the CSV file exported from Buttercup.
# Change this if your input file has a different name.
source = base / "pBMig"

# Name of the CSV file to generate for Bitwarden.
# Change this if you want a different output filename.
target = base / "bitwarden_con_carpetas.csv"
```

For example, if your Buttercup export is `buttercup.csv` in `~/Downloads`:

```python
base = Path.home() / "Downloads"
source = base / "buttercup.csv"
target = base / "bitwarden_import.csv"
```

The target file must not already exist: the script refuses to overwrite it. If you need to run the script again, use another output filename or move the previous output out of the way after checking what it contains.

## Run the converter

1. Export your vault from Buttercup as **Buttercup CSV**. Keep the original encrypted vault and a separate backup of the export until migration is verified.
2. Configure `base`, `source`, and `target` as described above.
3. Run:

   ```bash
   python3 convertir_buttercup_bitwarden.py
   ```

4. Check the printed counts of detected groups, converted entries, and folders containing entries. The script does not print passwords.

## Import into Bitwarden

In the Bitwarden web vault, open **Tools → Import**, select **Bitwarden (csv)** as the file format, and choose the generated CSV file. Do **not** select **Buttercup (csv)** for the converted file.

If you already imported the original Buttercup CSV, do not import the converted file on top of it without first dealing with the existing entries: another import can create duplicates. Be particularly careful with any existing data in your vault.

After importing, compare the entry count and inspect a sample of entries from different folders. Check their names, usernames, passwords, URLs, and notes before retiring Buttercup.

## Conversion details and limitations

- Buttercup groups are mapped to Bitwarden folder paths. Nested groups become paths such as `Personal/Email`.
- Only folders associated with imported entries appear; empty Buttercup groups are not created.
- Entries are imported as Bitwarden `login` items, regardless of how they were used in Buttercup.
- The title, username, and password are mapped to the corresponding Bitwarden fields.
- The first recognized URL is mapped to the login URL. Additional URLs are preserved in notes.
- Buttercup notes and other nonempty columns are preserved as text in the Bitwarden notes field. Extra fields are **not** recreated as interactive Bitwarden custom fields; review them after import.
- The converter does not move file attachments or passkeys. Check the original vault if you relied on either.

## Keep secrets out of Git

Do not commit vault exports or generated imports. Add patterns appropriate for your filenames to `.gitignore`, for example:

```gitignore
pBMig
pBMig (copia)
bitwarden_con_carpetas.csv
*.bcup
```

A `.gitignore` entry does not remove a secret that was already committed. If that happened, removing the file in a later commit is not enough: treat the exposed passwords as compromised and rotate them.

Once you have verified the migration, remove the unencrypted CSV files from your computer. Keep a secure backup of your encrypted original vault until you are confident nothing is missing.
