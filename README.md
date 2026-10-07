# SR Pool

Website für Poolbau, Pflege und Wartung in Berlin und Brandenburg.

Produktive Domain: https://sr-pool.de

## Aufbau

`python3 build_local_pages.py` erstellt die statische Website in `dist/`.
`python3 check_local_pages.py` prüft alle 66 Seiten einschließlich 54 Ortsseiten, Links, Metadaten und FAQ-Markup.

## Hetzner

Pushes auf `main` veröffentlichen `dist/` per SFTP. Benötigte Actions-Secrets: `HETZNER_HOST`, `HETZNER_USER`, `HETZNER_PORT`, `HETZNER_PASSWORD`. Optional `HETZNER_TARGET_DIR`, sonst wird in das für diese Website eingerichtete SFTP-Stammverzeichnis geladen. Der Workflow löscht keine entfernten Dateien.
