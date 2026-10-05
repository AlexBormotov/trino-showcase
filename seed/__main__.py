"""python -m seed: build tenant tables from data/synthea, write the manifest, load the stores."""

import json
from pathlib import Path

from seed.build import build
from seed.load import load_clinic_a, load_clinic_b, load_clinic_c

DATA = Path(__file__).resolve().parent.parent / "data"


def main() -> None:
    tenants, manifest = build(DATA / "synthea" / "csv")
    (DATA / "manifest.json").write_text(json.dumps(manifest, indent=2))
    for name, load in [("clinic_a", load_clinic_a), ("clinic_b", load_clinic_b), ("clinic_c", load_clinic_c)]:
        print(f"loading {name}")
        load(tenants[name].tables)
    print(json.dumps(manifest["tables"], indent=2))


if __name__ == "__main__":
    main()
