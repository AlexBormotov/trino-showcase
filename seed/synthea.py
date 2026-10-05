"""Generate the raw Synthea CSV export in a throwaway Java container.

Deterministic: fixed seeds and a fixed reference date, so the same run
produces the same patients regardless of the day it runs.
"""

import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

SYNTHEA_VERSION = "v4.0.0"
JAR_URL = (
    "https://github.com/synthetichealth/synthea/releases/download/"
    f"{SYNTHEA_VERSION}/synthea-with-dependencies.jar"
)
JAVA_IMAGE = "eclipse-temurin:17-jre"

DATA = Path(__file__).resolve().parent.parent / "data"
JAR = DATA / "cache" / f"synthea-{SYNTHEA_VERSION}.jar"
OUT = DATA / "synthea"


def main(population: int = 6000) -> None:
    if not JAR.exists():
        JAR.parent.mkdir(parents=True, exist_ok=True)
        print(f"downloading {JAR_URL}")
        tmp = JAR.with_suffix(".part")
        urllib.request.urlretrieve(JAR_URL, tmp)
        tmp.replace(JAR)

    shutil.rmtree(OUT, ignore_errors=True)
    cmd = [
        "docker", "run", "--rm",
        "-v", f"{DATA}:/data",
        JAVA_IMAGE,
        "java", "-jar", f"/data/cache/{JAR.name}",
        "-s", "42", "-cs", "42", "-r", "20261001",
        "-p", str(population),
        "--exporter.baseDirectory=/data/synthea",
        "--exporter.years_of_history=5",
        "--exporter.csv.export=true",
        "--exporter.csv.included_files=patients.csv,encounters.csv,conditions.csv,claims.csv,payers.csv",
        "--exporter.fhir.export=false",
        "--exporter.hospital.fhir.export=false",
        "--exporter.practitioner.fhir.export=false",
        "Massachusetts",
    ]
    subprocess.run(cmd, check=True)


if __name__ == "__main__":
    main(*(int(a) for a in sys.argv[1:]))
