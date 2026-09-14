# SOC 2 posture (honest)

Kraken-the-CLI on a laptop is not a SOC 2 system. SOC 2 applies when **topta.co** holds customer data (licenses, session pinboard, paid keys).

Map, not a certificate:

| TSC | What we do now | Gap |
|---|---|---|
| Security | 0600 keys, loopback Docker, no-new-privileges, hashed NIC | No signed catalog, no pentest |
| Availability | Local-first; API outage does not stop free arms | No SLA |
| Confidentiality | Vault + notes 0600; group key is a secret | Keys on disk, not OS keychain |
| Privacy | Free arms do not call home | License verify POSTs the key |
| Change mgmt | Tests + lockfile | No GH Actions until repo exists |

Do not put “SOC 2 certified” on the site. Put “designed against TSC; audit when billing is live.”
