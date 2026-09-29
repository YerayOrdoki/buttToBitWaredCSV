import csv
import os
from pathlib import Path

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
columns = ["folder", "favorite", "type", "name", "notes", "fields", "reprompt", "login_uri", "login_username", "login_password", "login_totp"]

if target.exists():
    raise SystemExit("El archivo de salida ya existe: no se sobrescribirá.")

with source.open("r", encoding="utf-8-sig", newline="") as f:
    reader = csv.DictReader(f)
    headers = reader.fieldnames or []
    required = {"!type", "!group_id", "!group_name", "!group_parent", "title", "username", "password"}
    if not required.issubset(headers):
        raise SystemExit("El CSV no contiene las columnas necesarias de Buttercup.")
    if len(headers) != len(set(headers)):
        raise SystemExit("Hay cabeceras duplicadas; no se puede convertir con seguridad.")
    rows = list(reader)

if any(None in row for row in rows):
    raise SystemExit("Hay filas con más columnas que la cabecera; revisa el CSV original.")
if any(None in row.values() for row in rows):
    raise SystemExit("Hay filas incompletas; revisa el CSV original.")

groups = {}
for row in rows:
    if row["!type"].strip().lower() == "group":
        gid = row["!group_id"].strip()
        if not gid or gid in groups or not row["!group_name"].strip():
            raise SystemExit("Hay identificadores de grupo duplicados o incompletos.")
        groups[gid] = (row["!group_name"].strip(), row["!group_parent"].strip())

paths = {}
def group_path(gid, visiting=None):
    if not gid or gid == "0":
        return ""
    if gid in paths:
        return paths[gid]
    if gid not in groups:
        raise ValueError("Hay una entrada asociada a un grupo ausente.")
    visiting = set() if visiting is None else visiting
    if gid in visiting:
        raise ValueError("Hay una referencia circular entre grupos.")
    visiting.add(gid)
    name, parent = groups[gid]
    if "/" in name:
        raise ValueError("Un nombre de grupo contiene '/', incompatible con carpetas anidadas.")
    prefix = group_path(parent, visiting)
    visiting.remove(gid)
    paths[gid] = f"{prefix}/{name}" if prefix else name
    return paths[gid]

try:
    for gid in groups:
        group_path(gid)
except ValueError as exc:
    raise SystemExit(str(exc))

reserved = {"!type", "!group_id", "!group_name", "!group_parent", "title", "username", "password", "id"}
url_keys = {"url", "uri", "website", "web", "login_uri"}
note_keys = {"note", "notes"}
totp_keys = {"totp", "otp", "login_totp"}
converted = []
for row in rows:
    kind = row["!type"].strip().lower()
    if kind == "group":
        continue
    if kind != "entry":
        raise SystemExit("Hay un tipo de fila no reconocido; no se ha escrito ningún archivo.")
    try:
        folder = group_path(row["!group_id"].strip())
    except ValueError as exc:
        raise SystemExit(str(exc))
    urls, notes, extras, totp = [], [], [], ""
    for key in headers:
        if key in reserved:
            continue
        value = row[key]
        if not value:
            continue
        label = key.strip()
        normal = label.casefold()
        if normal in url_keys:
            urls.append(value)
        elif normal in note_keys:
            notes.append(value)
        elif normal in totp_keys:
            if totp:
                extras.append(f"{label}: {value}")
            else:
                totp = value
        else:
            extras.append(f"{label}: {value}")
    if len(urls) > 1:
        extras.extend(f"URL adicional: {url}" for url in urls[1:])
    if extras:
        notes.append("Campos adicionales de Buttercup:\n" + "\n".join(extras))
    converted.append({
        "folder": folder,
        "favorite": "0",
        "type": "login",
        "name": row["title"],
        "notes": "\n\n".join(notes),
        "fields": "",
        "reprompt": "0",
        "login_uri": urls[0] if urls else "",
        "login_username": row["username"],
        "login_password": row["password"],
        "login_totp": totp,
    })

fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
with os.fdopen(fd, "w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=columns)
    writer.writeheader()
    writer.writerows(converted)

print(f"Grupos detectados: {len(groups)}")
print(f"Entradas convertidas: {len(converted)}")
print(f"Carpetas con entradas: {len({row['folder'] for row in converted if row['folder']})}")
print("Archivo generado: bitwarden_con_carpetas.csv (privado; contiene contraseñas).")
