# willys-skill

OpenClaw skill för Willys – hämtar kundvagn, orderhistorik, produktsök, leveranstider och profil direkt från ditt Willys-konto via deras REST API.

## Vad du kan göra

| Kommando i OpenClaw | Vad det gör |
|---------------------|-------------|
| `/willys cart` | Visar vad som ligger i kundvagnen just nu |
| `/willys orders` | Listar dina tidigare beställningar |
| `/willys search mjölk` | Söker efter produkter på Willys |
| `/willys slots` | Visar lediga leveranstider (kräver postnummer) |
| `/willys profile` | Visar din profil, e-post och bonuspoäng |

## Kom igång

### 1. Miljövariabler

Sätt dina inloggningsuppgifter innan du kör. Willys använder personnummer som användarnamn:

```bash
export WILLYS_EMAIL=197912060097
export WILLYS_PASSWORD=ditt-lösenord
export WILLYS_POSTAL_CODE=11234   # valfritt, krävs för leveranstider
```

### 2. Testa direkt med Python

```bash
# Profil
python3 skills/willys/willys.py profile

# Kundvagn
python3 skills/willys/willys.py cart

# Orderhistorik
python3 skills/willys/willys.py orders

# Produktsök
python3 skills/willys/willys.py search --query "mjölk"

# Leveranstider
python3 skills/willys/willys.py slots
```

All output är JSON till stdout. Vid fel returneras `{"error": "..."}`.

### 3. Via OpenClaw

Lägg `skills/willys/` i din OpenClaw skills-katalog så plockas skillet upp automatiskt. Anropa det sedan i chatten:

```
/willys cart
/willys orders
/willys search oatly
/willys profile
```

## Autentisering

Skillet loggar in mot `POST https://www.willys.se/login` med JSON-body:

```json
{
  "j_username": "<personnummer>",
  "j_password": "<lösenord>",
  "j_remember_me": true
}
```

Sessionen hålls vid liv med cookies under hela körningen. Inga credentials sparas eller loggas.

## API-endpoints som används

Alla endpoints ligger under `https://www.willys.se`:

| Funktion | Endpoint |
|----------|----------|
| Inloggning | `POST /login` |
| Kundvagn | `GET /axfood/rest/cart` |
| Orderhistorik | `GET /axfood/rest/account/orders` |
| Produktsök | `GET /search?q=...&size=20` |
| Leveranstider | `GET /tms/delivery-slots?postalCode=...` |
| Profil | `GET /axfood/rest/customer` |

## Filstruktur

```
skills/willys/
├── SKILL.md          # OpenClaw skill-definition (metadata, workflow, output-format)
├── willys.py         # Python-skraparen
└── local/
    ├── README.md     # Instruktioner för K8s-deployment av paketen
    └── lib/python3/site-packages/
        └── ...       # requests + beroenden (certifi, idna, charset-normalizer, urllib3)
```

## Python-beroenden

Skillet kräver bara `requests`. Paketet (med alla beroenden) är förbuntlat i `local/lib/python3/site-packages/` så att det fungerar i Kubernetes-pods utan att pip behöver vara installerat vid körning.

### Installera om du kör lokalt utan bunten

```bash
pip install requests
```

### Deploya till OpenClaw-pod (Kubernetes)

```bash
kubectl cp skills/willys/local/. openclaw-zoe-0:/root/.local -n openclaw-zoe
```

Se `skills/willys/local/README.md` för mer detaljer.

## Säkerhet

- **Read-only** – skillet gör inga ändringar, lägger inte till i vagnen och beställer ingenting.
- **Inga credentials i output** – användarnamn och lösenord skrivs aldrig ut i svar eller loggar.
- Credentials läses enbart från miljövariabler, aldrig från filer eller argument.
