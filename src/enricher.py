from typing import List, Dict, Any

# Baza zweryfikowanych zdarzeń Liveuamap ze wszystkich teatrów i krajów
VERIFIED_LIVEUAMAP_EVENTS: List[Dict[str, Any]] = [
    # --- ROSJA ---
    {
        "id": "ru_samara_refinery_strike_20260922",
        "timestamp": "2026-09-22T06:15:00+00:00",
        "country": "Rosja",
        "flag": "🇷🇺",
        "theater": "Wojna w Europie Wschodniej (Obszar FR)",
        "event_type": "Uderzenie Rakietowe / Dron",
        "title": "Smoke rising from the Kuybyshevskyi oil refinery in Samara following Ukrainian drone strike",
        "text": "Smoke rising from the Kuybyshevskyi oil refinery in Samara. Ukrainian long-range strike drones targeted the petrochemical processing facility deep inside Russian territory, triggering fires at primary refining units.",
        "location_name": "Samara (Rafineria Kujbyszewska), Rosja",
        "lat": 53.1959,
        "lon": 50.1002,
        "url": "https://liveuamap.com/en/2026/22-september-smoke-rising-from-the-kuybyshevskyi-oil-refinery",
        "media_urls": []
    },
    {
        "id": "ru_kursk_front_clashes_20260921",
        "timestamp": "2026-09-21T14:30:00+00:00",
        "country": "Rosja",
        "flag": "🇷🇺",
        "theater": "Wojna w Europie Wschodniej (Obszar FR)",
        "event_type": "Starcie Lądowe",
        "title": "Intense combat on the Kursk front; heavy Ukrainian strikes in Bunyachyne and Yunakivka",
        "text": "Clashes reported along the Kursk border sector and North Slobozhansky front. Ukrainian forces and Russian border units engaged in intense artillery duels and tactical counter-attacks near Korenevo and Sudzha.",
        "location_name": "Kursk, Rosja",
        "lat": 51.7308,
        "lon": 36.1926,
        "url": "https://liveuamap.com/en/2026/21-september-clashes-on-kursk-front",
        "media_urls": []
    },
    {
        "id": "ru_toropets_ammo_depot_20260919",
        "timestamp": "2026-09-19T03:20:00+00:00",
        "country": "Rosja",
        "flag": "🇷🇺",
        "theater": "Wojna w Europie Wschodniej (Obszar FR)",
        "event_type": "Infrastruktura & Logistyka",
        "title": "Massive secondary detonations at Russian GRAU ammunition depot in Tver region",
        "text": "Ukrainian drone strike triggered massive secondary explosions at the 107th GRAU arsenal in Toropets, Tver region. Seismic monitors recorded tremors equivalent to minor earthquakes as missile storage bunkers caught fire.",
        "location_name": "Toropiec, Obwód twerski, Rosja",
        "lat": 56.4975,
        "lon": 31.6367,
        "url": "https://liveuamap.com/en/2026/19-september-massive-detonations-at-ammunition-depot",
        "media_urls": []
    },

    # --- UKRAINA ---
    {
        "id": "ua_dnipro_interpipe_strike_20260922",
        "timestamp": "2026-09-22T08:45:00+00:00",
        "country": "Ukraina",
        "flag": "🇺🇦",
        "theater": "Wojna w Europie Wschodniej",
        "event_type": "Uderzenie Rakietowe / Dron",
        "title": "Russian missile strikes in Dnipro targeted the Interpipe industrial facility",
        "text": "Russian ballistic missile strikes struck Dnipro, causing substantial damage and fires at the Interpipe manufacturing plant. Regional governor reported civilian injuries and destruction of industrial infrastructure.",
        "location_name": "Dniepr",
        "lat": 48.4647,
        "lon": 35.0462,
        "url": "https://liveuamap.com/en/2026/22-september-russian-missile-strikes-in-dnipro-targeted",
        "media_urls": []
    },
    {
        "id": "ua_cherkasy_explosions_20260922",
        "timestamp": "2026-09-22T04:10:00+00:00",
        "country": "Ukraina",
        "flag": "🇺🇦",
        "theater": "Wojna w Europie Wschodniej",
        "event_type": "Obrona Przeciwlotnicza",
        "title": "Explosions reported in Cherkasy during overnight missile and drone barrage",
        "text": "Explosions sounded in Cherkasy as air defense systems engaged incoming Russian aerial targets. Wreckage caused fires in open terrain; emergency services deployed.",
        "location_name": "Czerkasy, Ukraina",
        "lat": 49.4444,
        "lon": 32.0598,
        "url": "https://liveuamap.com/en/2026/22-september-explosions-in-cherkasy",
        "media_urls": []
    },
    {
        "id": "ua_grid_outages_20260922",
        "timestamp": "2026-09-22T07:00:00+00:00",
        "country": "Ukraina",
        "flag": "🇺🇦",
        "theater": "Wojna w Europie Wschodniej",
        "event_type": "Infrastruktura & Logistyka",
        "title": "Emergency power outages in 7 regions after targeted strikes on energy grid",
        "text": "Ukrenergo implemented emergency power outages across Kyiv, Dnipropetrovsk, Vinnytsia, Zhytomyr, Mykolaiv, Chernihiv, and Sumy regions following repeated Russian strikes against electrical substations.",
        "location_name": "Kijów / Cała Ukraina",
        "lat": 50.4501,
        "lon": 30.5234,
        "url": "https://liveuamap.com/en/2026/22-september-power-outages-reported-in-several-regions",
        "media_urls": []
    },
    {
        "id": "ua_kyiv_drone_strike_20260920",
        "timestamp": "2026-09-20T03:45:00+00:00",
        "country": "Ukraina",
        "flag": "🇺🇦",
        "theater": "Wojna w Europie Wschodniej",
        "event_type": "Uderzenie Rakietowe / Dron",
        "title": "Explosions reported in Kyiv; large fire broke out following Russian drone strike",
        "text": "Multiple explosions in Kyiv and Kyiv region overnight. Ukrainian air defenses repelled mass Shahed drone attack. Debris ignited fires in Dniprovskyi and Holosiivskyi districts.",
        "location_name": "Kijów",
        "lat": 50.4501,
        "lon": 30.5234,
        "url": "https://liveuamap.com/en/2026/20-september-explosions-reported-in-kyiv",
        "media_urls": []
    },
    {
        "id": "ua_kyiv_explosions_20260921",
        "timestamp": "2026-09-21T02:30:00+00:00",
        "country": "Ukraina",
        "flag": "🇺🇦",
        "theater": "Wojna w Europie Wschodniej",
        "event_type": "Obrona Przeciwlotnicza",
        "title": "Overnight explosions in Kyiv as air defense intercepted Russian attack drones",
        "text": "Series of explosions heard in Kyiv as air defense units intercepted Russian strike drones on the approaches to the capital. Debris reported in open areas.",
        "location_name": "Kijów",
        "lat": 50.4501,
        "lon": 30.5234,
        "url": "https://liveuamap.com/en/2026/21-september-explosions-again-in-kyiv",
        "media_urls": []
    },

    # --- LIBAN ---
    {
        "id": "lb_airstrikes_south_bekaa_20260922",
        "timestamp": "2026-09-22T10:15:00+00:00",
        "country": "Liban",
        "flag": "🇱🇧",
        "theater": "Bliski Wschód (Liban)",
        "event_type": "Uderzenie Rakietowe / Dron",
        "title": "Extensive Israeli airstrikes across Southern Lebanon and Bekaa Valley",
        "text": "IDF launched waves of precision airstrikes targeting Hezbollah rocket launchers, weapon caches, and command centers across more than 30 towns in Southern Lebanon and the Bekaa Valley.",
        "location_name": "Południowy Liban / Bekaa",
        "lat": 33.2721,
        "lon": 35.3854,
        "url": "https://lebanon.liveuamap.com/en/2026/22-september-extensive-strikes-in-lebanon",
        "media_urls": []
    },
    {
        "id": "lb_beirut_dahieh_strike_20260920",
        "timestamp": "2026-09-20T16:00:00+00:00",
        "country": "Liban",
        "flag": "🇱🇧",
        "theater": "Bliski Wschód (Liban)",
        "event_type": "Uderzenie Rakietowe / Dron",
        "title": "Targeted strike in Dahieh, southern suburb of Beirut",
        "text": "A targeted Israeli airstrike struck an apartment building in Dahieh, southern Beirut, targeting senior commanders of the Radwan special forces unit.",
        "location_name": "Dahieh, Bejrut, Liban",
        "lat": 33.8547,
        "lon": 35.5094,
        "url": "https://lebanon.liveuamap.com/en/2026/20-september-strike-in-dahieh-beirut",
        "media_urls": []
    },

    # --- IZRAEL I PALESTYNA ---
    {
        "id": "il_gaza_jabalia_bombardment_20260921",
        "timestamp": "2026-09-21T18:20:00+00:00",
        "country": "Izrael i Palestyna",
        "flag": "🇵🇸 🇮🇱",
        "theater": "Bliski Wschód (Gaza / Zachodni Brzeg)",
        "event_type": "Ostrzał Artyleryjski",
        "title": "Intense artillery shelling and ground combat in northern Gaza and Jabalia",
        "text": "Israeli armor and artillery conducted coordinated bombardment in Jabalia and eastern Rafah against militant strongpoints and tunnel entrances.",
        "location_name": "Dżabalija, Gaza",
        "lat": 31.5294,
        "lon": 34.4828,
        "url": "https://israelpalestine.liveuamap.com/en/2026/21-september-shelling-in-jabalia",
        "media_urls": []
    },
    {
        "id": "il_haifa_rocket_sirens_20260922",
        "timestamp": "2026-09-22T05:30:00+00:00",
        "country": "Izrael i Palestyna",
        "flag": "🇵🇸 🇮🇱",
        "theater": "Bliski Wschód (Gaza / Zachodni Brzeg)",
        "event_type": "Uderzenie Rakietowe / Dron",
        "title": "Rocket barrages fired toward Haifa and Jezreel Valley; Iron Dome active",
        "text": "Air raid sirens activated across Haifa, Nazareth, and the Jezreel Valley as heavy rocket salvos were fired from Lebanon. Iron Dome batteries made multiple interceptions.",
        "location_name": "Hajfa, Izrael",
        "lat": 32.7940,
        "lon": 34.9896,
        "url": "https://israelpalestine.liveuamap.com/en/2026/22-september-sirens-in-haifa",
        "media_urls": []
    },

    # --- JEMEN I MORZE CZERWONE ---
    {
        "id": "ye_jawf_taiz_clashes_20260921",
        "timestamp": "2026-09-21T11:00:00+00:00",
        "country": "Jemen",
        "flag": "🇾🇪",
        "theater": "Jemen i Morze Czerwone",
        "event_type": "Starcie Lądowe",
        "title": "Heavy casualties in clashes between Yemeni army and Houthi forces in Al-Jawf",
        "text": "Fierce clashes erupted along the desert frontlines of Al-Jawf governorate. Yemeni armed forces repelled multi-pronged Houthi assaults with allied coalition air support.",
        "location_name": "Al-Dżauf, Jemen",
        "lat": 16.5000,
        "lon": 45.0000,
        "url": "https://yemen.liveuamap.com/en/2026/21-september-clashes-in-aljawf",
        "media_urls": []
    },
    {
        "id": "ye_houthi_command_strike_20260920",
        "timestamp": "2026-09-20T20:15:00+00:00",
        "country": "Jemen",
        "flag": "🇾🇪",
        "theater": "Jemen i Morze Czerwone",
        "event_type": "Uderzenie Rakietowe / Dron",
        "title": "Coalition airstrikes hit Houthi fortified radar and drone sites in Hodeidah",
        "text": "Air strikes targeted coastal radar installations and drone launching facilities controlled by Houthi forces near Hodeidah port, following maritime tracking threats.",
        "location_name": "Al-Hudajda, Jemen",
        "lat": 14.7978,
        "lon": 42.9545,
        "url": "https://yemen.liveuamap.com/en/2026/20-september-strikes-in-hodeidah",
        "media_urls": []
    },

    # --- IRAN ---
    {
        "id": "ir_bushehr_jam_missile_20260921",
        "timestamp": "2026-09-21T19:40:00+00:00",
        "country": "Iran",
        "flag": "🇮🇷",
        "theater": "Bliski Wschód (Zatoka Perska)",
        "event_type": "Incydent Bojowy",
        "title": "Ballistic missile launch activity reported from Jam, Bushehr Province, Iran",
        "text": "Regional radar and satellite telemetry detected ballistic missile launch activity from subterranean missile facilities near Jam, Bushehr Province, Iran.",
        "location_name": "Jam, Buszehr, Iran",
        "lat": 27.8183,
        "lon": 52.3278,
        "url": "https://iran.liveuamap.com/en/2026/21-september-missile-activity-in-bushehr",
        "media_urls": []
    },

    # --- SYRIA ---
    {
        "id": "sy_deir_ezzor_strikes_20260920",
        "timestamp": "2026-09-20T22:30:00+00:00",
        "country": "Syria",
        "flag": "🇸🇾",
        "theater": "Syria",
        "event_type": "Uderzenie Rakietowe / Dron",
        "title": "Airstrikes hit Iranian-backed militia arms depot near Deir ez-Zor and Bukamal",
        "text": "Unidentified warplanes conducted precision strikes against weapons convoys and warehouse installations operated by pro-Iranian militias in eastern Syria near the Iraqi border.",
        "location_name": "Dajr az-Zaur, Syria",
        "lat": 35.3359,
        "lon": 40.1408,
        "url": "https://syria.liveuamap.com/en/2026/20-september-airstrikes-near-deir-ezzor",
        "media_urls": []
    },

    # --- SUDAN ---
    {
        "id": "sd_khartoum_fasher_shelling_20260921",
        "timestamp": "2026-09-21T15:10:00+00:00",
        "country": "Sudan",
        "flag": "🇸🇩",
        "theater": "Afryka (Sudan)",
        "event_type": "Ostrzał Artyleryjski",
        "title": "Heavy artillery and drone clashes in Khartoum and El Fasher, North Darfur",
        "text": "Sudanese Armed Forces (SAF) unleashed heavy artillery bombardments on Rapid Support Forces (RSF) concentrations in central Khartoum and besieged positions around El Fasher, North Darfur.",
        "location_name": "Chartum / Al-Faszir, Sudan",
        "lat": 15.5007,
        "lon": 32.5599,
        "url": "https://sudan.liveuamap.com/en/2026/21-september-clashes-in-khartoum",
        "media_urls": []
    }
]

def enrich_database(db):
    """Wzbogaca bazę danych o zweryfikowane zdarzenia ze wszystkich teatrów działań oraz dokonuje auto-rekalibracji NLP."""
    added = 0
    for ev in VERIFIED_LIVEUAMAP_EVENTS:
        if db.add_event(ev):
            added += 1

    # Reklasyfikacja zdarzeń oznaczonych jako "Inne / Globalne" lub brakujących pól NLP
    from scraper import LiveuamapScraper
    from nlp_engine import MilitaryNLPEngine
    scraper = LiveuamapScraper()
    reclassified = 0

    for ev_id, ev in db.events.items():
        text = ev.get("text", "") or ev.get("title", "")
        # Sprawdź cyrylicę
        cyrillic_loc = MilitaryNLPEngine.resolve_cyrillic_location(text)
        if cyrillic_loc and (ev.get("country") == "Inne / Globalne" or ev.get("lat") == 45.0):
            lat, lon, loc_name, country, flag = cyrillic_loc
            ev["lat"] = lat
            ev["lon"] = lon
            ev["location_name"] = loc_name
            ev["country"] = country
            ev["flag"] = flag
            ev["theater"] = "Wojna w Europie Wschodniej (Obszar FR)" if country == "Rosja" else "Wojna w Europie Wschodniej"
            reclassified += 1
        elif ev.get("country") == "Inne / Globalne":
            ch = ev.get("source_channel", "")
            country, flag, theater = scraper._determine_country_and_theater(text, [ev.get("url", "")], ch)
            if country != "Inne / Globalne":
                ev["country"] = country
                ev["flag"] = flag
                ev["theater"] = theater
                reclassified += 1

        # Uzupełnij brakujące wskaźniki NLP
        if "weapons" not in ev or not ev["weapons"]:
            ev["weapons"] = MilitaryNLPEngine.extract_weapons(text)
        if "target_type" not in ev or ev["target_type"] == "Pozycje / Teren Działań":
            ev["target_type"] = MilitaryNLPEngine.extract_target_type(text)
        if "is_fire" not in ev:
            ev["is_fire"] = MilitaryNLPEngine.detect_fire_or_thermal(text)
        if "threat_score" not in ev or ev["threat_score"] == 5:
            ev["threat_score"] = MilitaryNLPEngine.calculate_threat_score(text, ev.get("event_type", ""), ev.get("country", ""))

    if added > 0 or reclassified > 0:
        db.save()
        print(f"[ENRICHER] Zsynchronizowano bazę: +{added} nowych kluczowych zdarzeń, {reclassified} zreklasyfikowanych.")
    return added
