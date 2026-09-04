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
from fallback_discovery import build_fallback_suggestions
from source_registry import SOURCES
from source_health import assess_source_health, source_health_summary
from sources import load_events
from ui_logic import DISCOVERY_DEFAULTS, compact_date_label, compact_location_label, date_matches, discovery_context_label, event_period_matches, price_label, price_matches
from ui_performance import INITIAL_RESULT_LIMIT, RESULT_BATCH_SIZE, clamp_result_limit, event_id_signature, next_result_limit, remaining_result_count, result_filter_signature

APP_VERSION = "0.27.0"

st.set_page_config(page_title="Upplevio", page_icon="✦", layout="wide")
st.markdown(
    """
<style>
:root{--ink:#111827;--muted:#6b7280;--line:#e5e7eb;--soft:#f7f7f5;--card:#fff}
.block-container{max-width:1180px;padding-top:1rem;padding-bottom:5rem}
[data-testid="stSidebar"]{background:#fafaf8}
.hero{padding:12px 2px 14px}.eyebrow{font-size:.72rem;font-weight:800;letter-spacing:.14em;text-transform:uppercase;color:#6b7280}
.hero h1{font-size:clamp(2.4rem,5vw,4.5rem);letter-spacing:-.055em;line-height:.95;margin:.25rem 0 .8rem;color:#111827}
.hero p{max-width:680px;color:#6b7280;font-size:1rem;line-height:1.5;margin-bottom:.2rem}.hero-kicker{font-size:.86rem;font-weight:750;color:#374151;margin-top:.45rem}
.flowbox{background:#fff;border:1px solid #e5e7eb;border-radius:24px;padding:18px;margin:4px 0 18px}
.section-title{font-size:1.45rem;font-weight:850;letter-spacing:-.03em;margin:28px 0 10px}
.result-summary{color:#6b7280;margin:.35rem 0 1rem}
.event-card{background:#fff;border:1px solid #e5e7eb;border-radius:20px;padding:16px;margin-bottom:10px;min-height:176px;box-shadow:0 1px 0 rgba(17,24,39,.02)}
.event-topline{display:flex;gap:8px;align-items:center;justify-content:space-between;margin-bottom:8px}.event-kind{font-size:.72rem;font-weight:800;letter-spacing:.05em;text-transform:uppercase;color:#6b7280}.event-flags{display:flex;gap:5px;flex-wrap:wrap;justify-content:flex-end}
.badge{display:inline-block;background:#f1f1ef;border-radius:999px;padding:4px 8px;font-size:.68rem;font-weight:800;color:#374151}
.badge-new{background:#111827;color:#fff}.badge-free{background:#e8f7ec;color:#176b34}.badge-warn{background:#fff1d6;color:#8a5a00}
.event-title{font-size:1.16rem;font-weight:850;letter-spacing:-.025em;margin:0 0 12px;line-height:1.2}
.quick-facts{display:grid;gap:7px}.quick-fact{display:flex;align-items:flex-start;gap:8px;color:#374151;font-size:.88rem;line-height:1.35}.fact-icon{width:1.05rem;flex:0 0 1.05rem;text-align:center}.fact-price{font-weight:800;color:#111827}.source{font-size:.72rem;color:#9ca3af;margin-top:10px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.detail-box{background:#fff;border:1px solid #e5e7eb;border-radius:20px;padding:22px;margin-top:12px}
div[data-testid="stButton"] button{border-radius:999px;min-height:42px}
@media(max-width:800px){
 .block-container{padding-left:.8rem;padding-right:.8rem}.hero h1{font-size:2.7rem}.flowbox{padding:14px}
 .event-card{min-height:auto;padding:15px}.event-title{font-size:1.12rem}.quick-fact{font-size:.9rem}.source{white-space:normal}.section-title{font-size:1.25rem}
}

.why { margin-top: .7rem; font-size: .82rem; font-weight: 650; color: #385c4a; }
.inline-detail{font-size:.88rem;line-height:1.55;color:#4b5563;padding:2px 1px 8px}.inline-detail p{margin:.7rem 0 0}.detail-trust{font-size:.76rem;color:#9ca3af}
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

@st.cache_data(ttl=900, show_spinner=False)
def cached_prepare_events(raw_event_list, source_health_value):
    prepared_events, prepared_review_pairs = deduplicate(raw_event_list)
    prepared_health = assess_source_health(source_health_value, raw_event_list)
    return prepared_events, prepared_review_pairs, prepared_health


events, review_pairs, health_assessments = cached_prepare_events(raw_events, source_health)
health_summary = source_health_summary(health_assessments)
today = date.today()

first_seen_before = event_first_seen_map()
visible_ingestion_ids = [e.id for e in events if not e.is_demo]
ingestion_signature = event_id_signature(visible_ingestion_ids)
if st.session_state.get("ingestion_signature") != ingestion_signature:
    record_event_sightings(visible_ingestion_ids)
    st.session_state["ingestion_signature"] = ingestion_signature
    first_seen = event_first_seen_map()
else:
    first_seen = first_seen_before
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
    flags = []
    if is_new(e):
        flags.append('<span class="badge badge-new">NY</span>')
    if e.price_status == "free":
        flags.append('<span class="badge badge-free">GRATIS</span>')
    warning = status_label(e)
    if warning:
        flags.append(f'<span class="badge badge-warn">{safe(warning.upper())}</span>')
    dist, geo_confidence = distance_info(e, origin_city) if origin_city and origin_city != "Hela Sverige" else (None, "unknown")
    date_text = compact_date_label(e, today)
    place_text = compact_location_label(e, dist, approximate=(geo_confidence == "city"))
    source_text = f'{verification_label(e)} · {", ".join(e.source_names)}'
    why_text = ""
    if rank_reasons:
        why_text = f'<div class="why">Varför högt: {safe(" · ".join(rank_reasons))}</div>'
    return f"""<div class="event-card">
    <div class="event-topline"><div class="event-kind">{safe(e.event_type)}</div><div class="event-flags">{''.join(flags)}</div></div>
    <div class="event-title">{safe(e.title)}</div>
    <div class="quick-facts">
      <div class="quick-fact"><span class="fact-icon">◷</span><span><b>{safe(date_text)}</b></span></div>
      <div class="quick-fact"><span class="fact-icon">⌖</span><span>{safe(place_text)}</span></div>
      <div class="quick-fact"><span class="fact-icon">◉</span><span class="fact-price">{safe(price_label(e))}</span></div>
    </div>
    {why_text}
    <div class="source">{safe(source_text)}</div></div>"""


def render_inline_details(e):
    date_text = compact_date_label(e, today)
    st.markdown(
        f"""<div class="inline-detail"><b>{safe(date_text)}</b><br>
        {safe(e.venue or "Plats ej angiven")}{safe((", " + e.city) if e.city else "")}<br>
        <b>{safe(price_label(e))}</b><br>
        <span class="detail-trust">{safe(verification_label(e))} · {safe(", ".join(e.source_names))}</span>
        {f'<p>{safe(e.description)}</p>' if e.description else ''}</div>""",
        unsafe_allow_html=True,
    )
    target_url = e.official_url or e.ticket_url
    if target_url:
        st.link_button("Öppna officiell sida", target_url, use_container_width=True)


future_events = [e for e in events if date.fromisoformat(e.end_date or e.start_date) >= today and not e.is_demo]
fav_ids = favorite_ids()

st.markdown(
    """<div class="hero"><div class="eyebrow">UPPLEVIO</div>
<h1>Hitta det du inte vill missa.</h1>
<p>Välj var du är och när du är ledig. Upplevio samlar riktiga evenemang från flera källor och sorterar det mest relevanta först.</p>
<div class="hero-kicker">Börja med plats och tid. Resten är valfritt.</div></div>""",
    unsafe_allow_html=True,
)

active_view = st.radio(
    "Vy", ["Upptäck", "Sparat", "Admin"], horizontal=True, label_visibility="collapsed", key="active_view"
)

if active_view == "Upptäck":
    if health_summary["has_public_warning"]:
        st.warning("Resultaten kan vara ofullständiga just nu. Någon datakälla behöver kontrolleras.")
    st.markdown('<div class="flowbox">', unsafe_allow_html=True)
    st.markdown("**Börja här**")
    city_choices = ["Hela Sverige"] + sorted(CITY_COORDS.keys())
    default_city = DISCOVERY_DEFAULTS["city"]
    default_city_index = city_choices.index(default_city) if default_city in city_choices else 0
    r1c1, r1c2 = st.columns(2)
    with r1c1:
        origin_city = st.selectbox("📍 Var?", city_choices, index=default_city_index)
    with r1c2:
        when_choices = ["Idag", "I helgen", "Nästa 7 dagar", "Nästa 30 dagar", "Nästa 3 månader"]
        default_when_index = when_choices.index(DISCOVERY_DEFAULTS["when"])
        when = st.selectbox("📅 När?", when_choices, index=default_when_index)

    r2c1, r2c2 = st.columns(2)
    with r2c1:
        radius_choices = [25, 50, 100, 200, 300]
        default_radius_index = radius_choices.index(DISCOVERY_DEFAULTS["radius_km"])
        radius_km = st.selectbox("🚗 Hur långt?", radius_choices, index=default_radius_index, disabled=(origin_city == "Hela Sverige"))
    with r2c2:
        price_choices = ["Alla priser", "Gratis", "Max 100 kr", "Max 250 kr", "Max 500 kr"]
        default_price_index = price_choices.index(DISCOVERY_DEFAULTS["price"])
        price_filter = st.selectbox("💰 Budget?", price_choices, index=default_price_index)

    with st.expander("Fler val", expanded=False):
        f1, f2 = st.columns(2)
        with f1:
            query = st.text_input("Sök", placeholder="Artist, mässa, arena eller ort…")
        with f2:
            types = ["Alla"] + sorted({e.event_type for e in future_events})
            type_filter = st.selectbox("Typ", types)
        only_new = st.toggle("Endast nytt i Upplevio")
        interests = st.multiselect(
            "Intressen (valfritt)",
            list(INTEREST_PROFILES.keys()),
            key="discovery_interests",
            placeholder="Musik, sport, familj…",
        )
        st.caption("Intressen påverkar bara sorteringen i den här sessionen. Event utanför dina val filtreras inte bort.")
    st.markdown('</div>', unsafe_allow_html=True)

    def matches(e):
        d = event_dt(e)
        if not event_period_matches(e, when, today):
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

    context_text = discovery_context_label(origin_city, when, None if origin_city == "Hela Sverige" else radius_km, price_filter)
    st.markdown(f'<div class="result-summary"><b>{len(filtered)}</b> event · {safe(context_text)}</div>', unsafe_allow_html=True)

    if not filtered:
        st.info("Inga event matchar exakt de här valen.")
        fallback_suggestions = build_fallback_suggestions(
            future_events,
            when=when,
            today=today,
            origin_city=origin_city,
            radius_km=radius_km,
            price_filter=price_filter,
            query=query,
            type_filter=type_filter,
            only_new=only_new,
            is_new=is_new,
            interests=interests,
        )
        if fallback_suggestions:
            st.markdown('<div class="section-title">Nära alternativ</div>', unsafe_allow_html=True)
            st.caption("Dina val ovan ändras inte. Här visas vad som blir möjligt om du lättar på ett tydligt filter i taget.")
            shown_fallback_ids = set()
            for suggestion in fallback_suggestions:
                fresh_events = [e for e in suggestion.events if e.id not in shown_fallback_ids]
                if not fresh_events:
                    continue
                st.markdown(f"**{suggestion.title}**")
                st.caption(suggestion.explanation)
                cols = st.columns(min(3, len(fresh_events)))
                for i, e in enumerate(fresh_events):
                    shown_fallback_ids.add(e.id)
                    with cols[i % len(cols)]:
                        st.markdown(card_markup(e, origin_city), unsafe_allow_html=True)
        else:
            st.caption("Upplevio hittar inga nära alternativ utan att ändra sökningen mer än rimligt. Prova att ta bort sökord eller eventtyp om du vill bredda ytterligare.")
    else:
        st.markdown('<div class="section-title">Bäst match först</div>', unsafe_allow_html=True)
        st.caption("Varje event visas en gång. NY och GRATIS markeras direkt på kortet.")
        filter_signature = result_filter_signature(
            origin_city=origin_city, when=when, radius_km=None if origin_city == "Hela Sverige" else radius_km,
            price_filter=price_filter, query=query, type_filter=type_filter, only_new=only_new, interests=interests,
        )
        if st.session_state.get("result_filter_signature") != filter_signature:
            st.session_state["result_filter_signature"] = filter_signature
            st.session_state["result_limit"] = INITIAL_RESULT_LIMIT

        visible_count = clamp_result_limit(len(filtered), st.session_state.get("result_limit"))
        visible_events = filtered[:visible_count]
        cols = st.columns(3)
        for i, e in enumerate(visible_events):
            with cols[i % 3]:
                st.markdown(card_markup(e, origin_city, rank_reasons.get(e.id)), unsafe_allow_html=True)
                with st.expander("Detaljer", expanded=False):
                    render_inline_details(e)
                label = "♥ Sparad" if e.id in fav_ids else "♡ Spara"
                if st.button(label, key=f"save-{e.id}", use_container_width=True):
                    toggle_favorite(e.id)
                    st.rerun()

        remaining = remaining_result_count(len(filtered), visible_count)
        if remaining:
            next_batch = min(RESULT_BATCH_SIZE, remaining)
            if st.button(f"Visa {next_batch} till · {remaining} kvar", key="show-more-results", use_container_width=True):
                st.session_state["result_limit"] = next_result_limit(len(filtered), visible_count)
                st.rerun()

elif active_view == "Sparat":
    saved = sorted([e for e in future_events if e.id in fav_ids], key=event_dt)
    st.markdown('<div class="section-title">Sparade event</div>', unsafe_allow_html=True)
    if not saved:
        st.info("Du har inte sparat några event ännu.")
    else:
        cols = st.columns(3)
        for i, e in enumerate(saved):
            with cols[i % 3]:
                st.markdown(card_markup(e), unsafe_allow_html=True)
                with st.expander("Detaljer", expanded=False):
                    render_inline_details(e)
                if st.button("Ta bort sparad", key=f"saved-remove-{e.id}", use_container_width=True):
                    toggle_favorite(e.id)
                    st.rerun()

elif active_view == "Admin":
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
    h1, h2, h3 = st.columns(3)
    h1.metric("Källor med fel", health_summary["counts"].get("Fel", 0))
    h2.metric("Behöver kontrolleras", health_summary["counts"].get("Kontrollera", 0))
    h3.metric("Säsongstomma", health_summary["counts"].get("Säsongstom", 0))
    st.dataframe(pd.DataFrame([{
        "Källa": x.source, "Status": x.state, "Importerade": x.imported, "Diagnos": x.summary
    } for x in health_assessments]), use_container_width=True, hide_index=True)
    st.caption("Diagnosen gäller aktuell import. Historisk volymavvikelse kräver senare schemalagda importer och en persistent källhistorik.")
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
