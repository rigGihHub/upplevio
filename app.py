import html
import os
from datetime import date, datetime, timedelta, timezone

import pandas as pd
import streamlit as st

from coverage import coverage_snapshot
from benchmark import benchmark_report, load_benchmark
from geography import CITY_COORDS, distance_from_city, distance_info
from db import event_first_seen_map, favorite_ids, record_event_sightings, toggle_favorite
from dedupe import deduplicate, verification_label
from discovery import INTEREST_PROFILES, event_matches_query, rank_discovery
from source_registry import SOURCES
from sources import load_events
from ui_logic import date_matches, price_label, price_matches

APP_VERSION = "0.18.0"

st.set_page_config(page_title="Upplevio", page_icon="✦", layout="wide")
st.markdown(
    """
<style>
:root{--ink:#111827;--muted:#6b7280;--line:#e5e7eb;--soft:#f7f7f5;--card:#fff}
.block-container{max-width:1180px;padding-top:1rem;padding-bottom:5rem}
[data-testid="stSidebar"]{background:#fafaf8}
.hero{padding:18px 2px 18px}.eyebrow{font-size:.72rem;font-weight:800;letter-spacing:.14em;text-transform:uppercase;color:#6b7280}
.hero h1{font-size:clamp(2.4rem,5vw,4.5rem);letter-spacing:-.055em;line-height:.95;margin:.25rem 0 .8rem;color:#111827}
.hero p{max-width:720px;color:#6b7280;font-size:1.02rem;line-height:1.6}
.flowbox{background:#fff;border:1px solid #e5e7eb;border-radius:24px;padding:18px;margin:4px 0 18px}
.section-title{font-size:1.45rem;font-weight:850;letter-spacing:-.03em;margin:28px 0 10px}
.result-summary{color:#6b7280;margin:.35rem 0 1rem}
.event-card{background:#fff;border:1px solid #e5e7eb;border-radius:20px;padding:17px;margin-bottom:10px;min-height:190px;box-shadow:0 1px 0 rgba(17,24,39,.02)}
.badge{display:inline-block;background:#f1f1ef;border-radius:999px;padding:5px 9px;font-size:.72rem;font-weight:750;margin:0 4px 4px 0;color:#374151}
.badge-new{background:#111827;color:#fff}.badge-free{background:#e8f7ec;color:#176b34}.badge-warn{background:#fff1d6;color:#8a5a00}
.event-title{font-size:1.18rem;font-weight:850;letter-spacing:-.025em;margin:10px 0 6px;line-height:1.22}
.event-meta{color:#4b5563;font-size:.88rem;line-height:1.65}.source{font-size:.74rem;color:#9ca3af;margin-top:10px}
.detail-box{background:#fff;border:1px solid #e5e7eb;border-radius:20px;padding:22px;margin-top:12px}
div[data-testid="stButton"] button{border-radius:999px;min-height:42px}
@media(max-width:800px){
 .block-container{padding-left:.8rem;padding-right:.8rem}.hero h1{font-size:2.7rem}.flowbox{padding:14px}
 .event-card{min-height:auto}.section-title{font-size:1.25rem}
}

.why { margin-top: .7rem; font-size: .82rem; font-weight: 650; color: #385c4a; }
</style>
""",
    unsafe_allow_html=True,
)


def secret(name):
    try:
        return st.secrets.get(name)
    except Exception:
        return os.getenv(name)


api_key = secret("TICKETMASTER_API_KEY")
demo_mode = str(secret("UPPLEVIO_DEMO_MODE") or "").strip().lower() in {"1", "true", "yes", "on"}

# Technical source switches are intentionally hidden from the normal discovery flow.
with st.sidebar.expander("Utvecklarinställningar", expanded=False):
    st.caption("För test och datakvalitet – inte en del av den vanliga användarresan.")
    experimental_sources = st.toggle("Officiella mässkalendrar", value=False)
    experimental_collectors = st.toggle("Samlarkort/retro-källor", value=False)
    experimental_entertainment = st.toggle("Stand-up/scenkällor", value=False)

experimental_keys = ["stockholmsmassan", "elmia", "malmomassan"] if experimental_sources else []
collector_keys = ["kortcentralen", "tickster_collectors"] if experimental_collectors else []
entertainment_keys = ["showtic"] if experimental_entertainment else []


@st.cache_data(ttl=900, show_spinner=False)
def cached_load_events(api_key_value, official_keys, collector_source_keys, entertainment_source_keys, include_demo_value):
    return load_events(
        api_key_value,
        include_visitsweden=True,
        include_conventum=True,
        experimental_official_keys=list(official_keys),
        experimental_collector_keys=list(collector_source_keys),
        experimental_entertainment_keys=list(entertainment_source_keys),
        include_demo=include_demo_value,
    )


with st.spinner("Hämtar aktuella evenemang…"):
    raw_events, source_health = cached_load_events(
        api_key,
        tuple(experimental_keys),
        tuple(collector_keys),
        tuple(entertainment_keys),
        demo_mode,
    )

events, review_pairs = deduplicate(raw_events)
today = date.today()

first_seen_before = event_first_seen_map()
record_event_sightings([e.id for e in events if not e.is_demo])
first_seen = event_first_seen_map()
new_cutoff = datetime.now(timezone.utc) - timedelta(days=7)


def event_dt(e):
    try:
        return date.fromisoformat(e.start_date)
    except Exception:
        return date.max


def is_new(e):
    if e.is_demo:
        return False
    raw = first_seen_before.get(e.id) or first_seen.get(e.id)
    if not raw:
        return False
    try:
        seen = datetime.fromisoformat(raw)
        if seen.tzinfo is None:
            seen = seen.replace(tzinfo=timezone.utc)
        return seen >= new_cutoff
    except Exception:
        return False


def fmt_date(d):
    months = ["jan", "feb", "mar", "apr", "maj", "jun", "jul", "aug", "sep", "okt", "nov", "dec"]
    return f"{d.day} {months[d.month - 1]} {d.year}"


def safe(value):
    return html.escape(str(value or ""), quote=True)


def status_label(e):
    status = (e.status or "unknown").lower()
    if status in {"cancelled", "canceled"}:
        return "Inställt"
    if status in {"postponed"}:
        return "Uppskjutet"
    if status in {"rescheduled"}:
        return "Flyttat"
    return ""


def card_markup(e, origin_city=None, rank_reasons=None):
    badges = [f'<span class="badge">{safe(e.event_type)}</span>']
    if is_new(e):
        badges.insert(0, '<span class="badge badge-new">NY</span>')
    if e.price_status == "free":
        badges.append('<span class="badge badge-free">GRATIS</span>')
    warning = status_label(e)
    if warning:
        badges.append(f'<span class="badge badge-warn">{safe(warning.upper())}</span>')
    dist, geo_confidence = distance_info(e, origin_city) if origin_city and origin_city != "Hela Sverige" else (None, "unknown")
    if dist is None:
        dist_text = ""
    elif geo_confidence == "city":
        dist_text = f" · ca {dist} km bort"
    else:
        dist_text = f" · {dist} km bort"
    source_text = f'{verification_label(e)} · {", ".join(e.source_names)}'
    why_text = ""
    if rank_reasons:
        why_text = f'<div class="why">Varför högt: {safe(" · ".join(rank_reasons))}</div>'
    return f"""<div class="event-card">{''.join(badges)}
    <div class="event-title">{safe(e.title)}</div>
    <div class="event-meta"><b>{safe(fmt_date(event_dt(e)))}</b><br>
    {safe(e.venue or "Plats ej angiven")} · {safe(e.city or "Ort saknas")}{safe(dist_text)}<br>
    {safe(price_label(e))}</div>
    {why_text}
    <div class="source">{safe(source_text)}</div></div>"""


future_events = [e for e in events if event_dt(e) >= today and not e.is_demo]
fav_ids = favorite_ids()

st.markdown(
    """<div class="hero"><div class="eyebrow">UPPLEVIO</div>
<h1>Vad händer?</h1>
<p>Välj var du är och när du är ledig. Upplevio samlar riktiga evenemang från flera källor och hjälper dig hitta sådant du annars hade missat.</p></div>""",
    unsafe_allow_html=True,
)

main_tab, saved_tab, admin_tab = st.tabs(["Vad händer?", "Sparat", "Admin"])

with main_tab:
    st.markdown('<div class="flowbox">', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns([1.25, 1.25, 1, 1])
    city_choices = ["Hela Sverige"] + sorted(CITY_COORDS.keys())
    default_city_index = city_choices.index("Örebro") if "Örebro" in city_choices else 0
    with c1:
        origin_city = st.selectbox("📍 Var?", city_choices, index=default_city_index)
    with c2:
        when = st.selectbox("📅 När?", ["Idag", "I helgen", "Nästa 7 dagar", "Nästa 30 dagar", "Nästa 3 månader"], index=3)
    with c3:
        radius_km = st.selectbox("🚗 Hur långt?", [25, 50, 100, 200, 300], index=2, disabled=(origin_city == "Hela Sverige"))
    with c4:
        price_filter = st.selectbox("💰 Budget?", ["Alla priser", "Gratis", "Max 100 kr", "Max 250 kr", "Max 500 kr"])

    with st.expander("Dina intressen (valfritt)", expanded=False):
        interests = st.multiselect(
            "Vad brukar du vilja hitta?",
            list(INTEREST_PROFILES.keys()),
            key="discovery_interests",
            placeholder="Välj ett eller flera intressen…",
        )
        st.caption("Används bara för att sortera resultaten bättre i den här sessionen. Du missar inte event utanför dina val.")

    with st.expander("Fler filter", expanded=False):
        f1, f2 = st.columns(2)
        with f1:
            query = st.text_input("Sök", placeholder="Artist, mässa, arena eller ort…")
        with f2:
            types = ["Alla"] + sorted({e.event_type for e in future_events})
            type_filter = st.selectbox("Typ", types)
        only_new = st.toggle("Endast nytt i Upplevio")
    st.markdown('</div>', unsafe_allow_html=True)

    def matches(e):
        d = event_dt(e)
        if not date_matches(d, when, today):
            return False
        if type_filter != "Alla" and e.event_type != type_filter:
            return False
        if only_new and not is_new(e):
            return False
        if not price_matches(e, price_filter):
            return False
        if origin_city != "Hela Sverige":
            dist = distance_from_city(e, origin_city)
            if dist is None or dist > radius_km:
                return False
        if query and not event_matches_query(e, query):
            return False
        return True

    filtered = [e for e in future_events if matches(e)]
    ranked_results = rank_discovery(filtered, origin_city=origin_city, price_filter=price_filter, query=query, today=today, interests=interests)
    filtered = [e for _, e in ranked_results]
    rank_reasons = {e.id: rank.reasons for rank, e in ranked_results}

    location_text = origin_city if origin_city != "Hela Sverige" else "hela Sverige"
    st.markdown(f'<div class="result-summary"><b>{len(filtered)}</b> event matchar · {safe(location_text)} · {safe(when.lower())}</div>', unsafe_allow_html=True)

    if not filtered:
        st.info("Inga event matchar just de här valen. Prova större radie, längre period eller alla priser.")
    else:
        if any(is_new(e) for e in filtered):
            st.markdown('<div class="section-title">Nytt i Upplevio</div>', unsafe_allow_html=True)
            new_rows = [e for e in filtered if is_new(e)][:6]
            cols = st.columns(3)
            for i, e in enumerate(new_rows):
                with cols[i % 3]:
                    st.markdown(card_markup(e, origin_city), unsafe_allow_html=True)
                    if st.button("♡ Spara" if e.id not in fav_ids else "♥ Sparad", key=f"new-save-{e.id}", use_container_width=True):
                        toggle_favorite(e.id)
                        st.rerun()

        free_rows = [e for e in filtered if e.price_status == "free"][:6]
        if free_rows and price_filter == "Alla priser":
            st.markdown('<div class="section-title">Gratis nära dig</div>', unsafe_allow_html=True)
            cols = st.columns(3)
            for i, e in enumerate(free_rows):
                with cols[i % 3]:
                    st.markdown(card_markup(e, origin_city), unsafe_allow_html=True)

        st.markdown('<div class="section-title">Bäst match först</div>', unsafe_allow_html=True)
        cols = st.columns(3)
        for i, e in enumerate(filtered):
            with cols[i % 3]:
                st.markdown(card_markup(e, origin_city, rank_reasons.get(e.id)), unsafe_allow_html=True)
                b1, b2 = st.columns(2)
                if b1.button("Detaljer", key=f"detail-{e.id}", use_container_width=True):
                    st.session_state["selected_event"] = e.id
                label = "♥ Sparad" if e.id in fav_ids else "♡ Spara"
                if b2.button(label, key=f"save-{e.id}", use_container_width=True):
                    toggle_favorite(e.id)
                    st.rerun()

        selected = next((e for e in events if e.id == st.session_state.get("selected_event")), None)
        if selected:
            st.markdown('<div class="section-title">Detaljer</div>', unsafe_allow_html=True)
            st.markdown(
                f"""<div class="detail-box"><div class="eyebrow">{safe(selected.event_type)} · {safe(selected.category)}</div>
                <div class="event-title" style="font-size:1.8rem">{safe(selected.title)}</div>
                <div class="event-meta"><b>Datum:</b> {safe(selected.start_date)}{safe((" · " + selected.start_time) if selected.start_time else "")}<br>
                <b>Plats:</b> {safe(selected.venue or "Ej angiven")}, {safe(selected.city or "Ort saknas")}<br>
                <b>Pris:</b> {safe(price_label(selected))}<br>
                <b>Källor:</b> {safe(", ".join(selected.source_names))}<br>
                <b>Senast verifierad:</b> {safe(selected.verified_at or "okänt")}</div>
                <p>{safe(selected.description or "Ingen beskrivning tillgänglig.")}</p></div>""",
                unsafe_allow_html=True,
            )
            if selected.official_url:
                st.link_button("Officiell sida", selected.official_url)

with saved_tab:
    saved = sorted([e for e in future_events if e.id in fav_ids], key=event_dt)
    st.markdown('<div class="section-title">Sparade event</div>', unsafe_allow_html=True)
    if not saved:
        st.info("Du har inte sparat några event ännu.")
    else:
        cols = st.columns(3)
        for i, e in enumerate(saved):
            with cols[i % 3]:
                st.markdown(card_markup(e), unsafe_allow_html=True)

with admin_tab:
    st.caption("Datakvalitet och teknisk diagnostik. Den här informationen påverkar inte den vanliga användarresan.")
    cov = coverage_snapshot(events, review_pairs, horizon_days=30)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Event · 30 dagar", cov["events"])
    c2.metric("Flera källor", cov["multi_source"])
    c3.metric("Saknar exakt plats", cov["missing_coordinates"])
    c4.metric("Dublettkandidater", cov["duplicate_candidates"])
    st.caption("Datadiagnos – inte ett påstående om andelen av alla verkliga event som Upplevio täcker.")

    st.markdown("### Örebro benchmark · oberoende referensmängd")
    benchmark_path = os.path.join(os.path.dirname(__file__), "data", "benchmark_orebro_2026-09.csv")
    try:
        benchmark_events = load_benchmark(benchmark_path)
        bench = benchmark_report(benchmark_events, events)
        b1, b2, b3 = st.columns(3)
        b1.metric("Referensevent", bench["reference_events"])
        b2.metric("Hittade av Upplevio", bench["matched"])
        b3.metric("Benchmark-täckning", f"{bench['coverage_percent']:.1f}%" if bench["coverage_percent"] is not None else "–")
        if bench.get("by_reference_source"):
            source_rows = []
            for source_name, stats in sorted(bench["by_reference_source"].items()):
                source_rows.append({
                    "Referenskälla": source_name,
                    "Referensevent": stats["reference_events"],
                    "Hittade": stats["matched"],
                    "Missade": stats["missed"],
                    "Täckning": f'{stats["coverage_percent"]:.1f}%' if stats["coverage_percent"] is not None else "–",
                })
            st.dataframe(pd.DataFrame(source_rows), hide_index=True, use_container_width=True)
        st.caption(
            "Avser endast den manuellt kontrollerade referensmängden för Örebro 4 sep–3 okt 2026, "
            "kontrollerad 3 sep 2026 mot Visit Örebro och Conventum. Det är inte marknadstäckning för alla event i Örebro."
        )
        if bench["missed_events"]:
            with st.expander(f"Missade benchmark-event ({bench['missed']})", expanded=True):
                rows = [{
                    "Datum": x.start_date, "Event": x.title, "Plats": x.venue,
                    "Referens": x.reference_source, "Kontrollerad": x.checked_at
                } for x in bench["missed_events"]]
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else:
            st.success("Alla event i den aktuella benchmark-referensen hittades i importen.")
    except Exception as exc:
        st.warning(f"Benchmark kunde inte läsas: {exc}")
    st.markdown("### Källstatus")
    st.dataframe(pd.DataFrame(source_health, columns=["Källa", "Status", "Importerade", "Kommentar"]), use_container_width=True, hide_index=True)
    if cov["sources"]:
        st.markdown("### Källfördelning")
        st.dataframe(pd.DataFrame([{"Källa": k, "Event kommande 30 dagar": v} for k, v in cov["sources"].items()]), use_container_width=True, hide_index=True)
    with st.expander("Möjliga dubletter"):
        if not review_pairs:
            st.success("Inga tveksamma dublettkandidater i aktuell import.")
        else:
            rows = [{"A": a.title, "B": b.title, "Datum": a.start_date, "Ort": a.city or b.city, "Likhet": f"{score:.0%}"} for a, b, score in review_pairs]
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    with st.expander("Källregister"):
        rows = [{"Källa": x.name, "Typ": x.source_type, "Täcker": x.coverage, "Ort": x.city or "Nationellt", "Tillitsnivå": x.trust_level, "Import": x.import_mode} for x in SOURCES]
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

st.caption(f"Upplevio v{APP_VERSION} · Upptäck mer. Upplev mer.")
