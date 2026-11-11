# Kodeks.me plugin

Crnogorski propisi i sudska praksa sa [kodeks.me](https://kodeks.me) u vašem Claude-u ili ChatGPT-u. Plugin donosi konektor (alati za pretragu i čitanje propisa i presuda) i dva skilla:

- **pravno-misljenje** — pravno mišljenje o predmetu iz priloženih dokumenata: odlučujuća pitanja, argumenti obje strane sa doslovnim citatima propisa i sudske prakse, hronologija i rokovi, scenariji i procjena ishoda, kao Word dokument. Svaki citat propisa i presude provjerava kodeks.me, a svaki citat iz dokumenata predmeta provjerava skripta na vašem računaru, po istim pravilima.
- **provjera-citata** — provjera citata propisa i presuda u podnesku ili nacrtu.

Dokumenti predmeta ostaju u vašem asistentu: kodeks.me prima samo pravne pojmove za pretragu i citate javnih tekstova za provjeru. Analizu radi vaš asistent na vašoj pretplati; kodeks.me provjerava doslovnost citata, ne i zaključivanje. Svaki dokument je nacrt koji advokat provjerava.

## Uslovi

- Nalog na kodeks.me sa paketom Konektor ili Kompletni.
- Claude (plan koji podržava konektore i skillove, uz uključeno izvršavanje koda) ili ChatGPT sa podrškom za prilagođene konektore.

## Instalacija u Claude

1. Settings → Connectors → Add custom connector, adresa `https://kodeks.me/mcp`, pa Connect: prijavite se na kodeks.me (lozinka i kod iz authenticator aplikacije) i odobrite pristup.
2. Dodajte plugin: Customize → Plugins → Add marketplace, upišite `strahinja-radman/kodeks-plugin` i instalirajte plugin **kodeks**. U Claude Code: `/plugin marketplace add strahinja-radman/kodeks-plugin`, pa `/plugin install kodeks@kodeks`.
3. U razgovoru priložite dokumente predmeta i pokrenite `/pravno-misljenje` ili zatražite pravno mišljenje.

## Licenca

MIT, vidi [LICENSE](LICENSE). Konektor i baza propisa i sudske prakse su usluga kodeks.me i traže pretplatu.

## Razvoj

Izvor plugina je `plugins/kodeks` u repozitorijumu kodeks.me; ovaj javni repozitorijum se ažurira skriptom `plugins/kodeks/publish.sh`.


Testovi skripti (pravila citata su ista kao na serveru, iz `backend/internal/analysis/testdata/quote_vectors.json`):

```
python3 -m unittest discover -s plugins/kodeks/tests
```

Paket za otpremanje: `plugins/kodeks/build.sh` pravi `dist/kodeks-plugin.zip`.

---

Montenegrin legislation and case law from kodeks.me in your assistant: a connector with read-only corpus tools, a legal-opinion skill whose legal quotations kodeks.me verifies and whose document quotations a local script verifies, and a quotation-check skill. Case documents never leave the assistant.
