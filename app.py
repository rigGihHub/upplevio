import html
import os
from datetime import date, datetime, timedelta, timezone

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from coverage import coverage_snapshot
from benchmark import benchmark_report, benchmark_sample_quality, load_benchmark
from geography import CITY_COORDS, distance_from_city, distance_info
from db import event_first_seen_map, favorite_ids, record_event_sightings, toggle_favorite
from dedupe import collapse_productions, deduplicate, verification_label
from discovery import INTEREST_PROFILES, event_matches_query, rank_discovery
from discovery_quality import discovery_quality_report
from discovery_data_quality import discovery_data_quality_report
from fallback_discovery import build_fallback_suggestions
from source_registry import SOURCES
from source_health import assess_source_health, source_health_summary
from source_value import source_value_report
from local_source_audit import local_source_audit
from detail_coverage import detail_coverage_audit
from detail_gap_prioritizer import detail_gap_priorities
from detail_gap_workflow import detail_gap_cases, gap_workflow_summary
from parser_fix_evidence import fetch_gap_evidence
from parser_evidence_batch import evidence_batch_audit
from parser_fix_recommendation import build_parser_fix_recommendation
from parser_fix_impact import parser_fix_impact_audit
from parser_guardrails import run_guardrail_registry
from coverage_frontier import coverage_frontier
from candidate_local_sources import fetch_candidate_sources, candidate_value_audit
from candidate_decision import record_candidate_snapshot, candidate_decisions, candidate_history
from candidate_portfolio import candidate_portfolio
from result_trust import is_high_confidence_noise, result_trust_report
from discovery_value import is_local_discovery_tip
from engagement import booking_target, primary_info_target, company_metrics, record_action
from booking_intent import booking_cta, cta_quality
from booking_coverage import booking_coverage_report
from booking_partners import apply_booking_partner_attribution, partner_report
from ad_inventory import AD_SLOTS
from conversion_attribution import attribution_report
from tracked_redirect import build_tracked_url, process_redirect
from funnel_intelligence import funnel_report, session_impression_key
from showtimes import showtime_status, evening_match
from tonight_mode import tonight_shortlist, tonight_remaining, tonight_summary
from last_minute import last_minute_info, last_minute_match, last_minute_shortlist, last_minute_remaining
from go_now import go_now_info, go_now_match, go_now_shortlist, go_now_remaining
from sources import load_events
from ui_logic import DISCOVERY_DEFAULTS, compact_date_label, compact_location_label, date_matches, discovery_context_label, event_period_matches, price_label, price_matches
from ui_performance import INITIAL_RESULT_LIMIT, RESULT_BATCH_SIZE, clamp_result_limit, event_id_signature, next_result_limit, remaining_result_count, result_filter_signature

APP_VERSION = "0.85.0"

st.set_page_config(page_title="Upplevio", page_icon="✦", layout="wide")
st.markdown(
    """
<style>
:root{
  --night:#080716;
  --night-2:#111027;
  --panel:#15142b;
  --panel-2:#1b1936;
  --ink:#fff9eb;
  --muted:#c7bfd9;
  --line:rgba(255,255,255,.14);
  --pink:#ff4fd8;
  --cyan:#67e8f9;
  --lime:#d9ff67;
  --gold:#ffd76a;
  --violet:#8b5cf6;
}
html,body,[data-testid="stAppViewContainer"]{
  background:
    radial-gradient(circle at 12% 8%, rgba(255,79,216,.18), transparent 26rem),
    radial-gradient(circle at 84% 12%, rgba(103,232,249,.14), transparent 28rem),
    radial-gradient(circle at 50% 95%, rgba(139,92,246,.16), transparent 34rem),
    linear-gradient(180deg,#080716 0%,#0d0b1d 55%,#090817 100%);
  color:var(--ink);
}
[data-testid="stAppViewContainer"]::before{
  content:"";
  position:fixed; inset:0; pointer-events:none; z-index:0; opacity:.22;
  background-image:
    linear-gradient(rgba(255,255,255,.025) 1px,transparent 1px),
    linear-gradient(90deg,rgba(255,255,255,.025) 1px,transparent 1px);
  background-size:36px 36px;
  mask-image:linear-gradient(to bottom,black,transparent 78%);
}
.block-container{max-width:1440px;padding-top:.5rem;padding-bottom:4rem;position:relative;z-index:1}
[data-testid="stSidebar"]{
  background:linear-gradient(180deg,#0d0b1f,#111027);
  border-right:1px solid rgba(255,255,255,.09)
}
[data-testid="stSidebar"] *{color:var(--ink)}
[data-testid="stHeader"]{background:rgba(8,7,22,.72);backdrop-filter:blur(16px)}

.hero{
  position:relative; overflow:hidden; padding:18px 22px 16px; margin:2px 0 10px;
  border:1px solid rgba(255,255,255,.18); border-radius:32px;
  background:
    radial-gradient(circle at 78% 20%,rgba(103,232,249,.19),transparent 26%),
    radial-gradient(circle at 15% 80%,rgba(255,79,216,.24),transparent 30%),
    linear-gradient(135deg,rgba(28,25,58,.96),rgba(12,10,31,.98));
  box-shadow:0 22px 70px rgba(0,0,0,.28), inset 0 0 50px rgba(255,255,255,.018);
}
.hero::before{
  content:""; position:absolute; width:320px; height:320px; right:-85px; top:-125px;
  border:22px solid rgba(255,215,106,.16); border-radius:50%;
  box-shadow:0 0 0 28px rgba(255,79,216,.07),0 0 0 58px rgba(103,232,249,.04);
}
.hero::after{
  content:"✦  ✦  ✦  ✦  ✦"; position:absolute; right:22px; bottom:18px;
  color:rgba(217,255,103,.58); letter-spacing:.7rem; transform:rotate(-8deg); font-size:.9rem
}
.eyebrow{
  display:inline-flex;align-items:center;gap:8px;
  font-size:.72rem;font-weight:900;letter-spacing:.16em;text-transform:uppercase;
  color:#0c0a1d;background:var(--lime);border-radius:999px;padding:7px 11px;
  box-shadow:0 0 22px rgba(217,255,103,.22)
}
.hero h1{
  max-width:900px;font-size:clamp(2.2rem,4.2vw,3.75rem);letter-spacing:-.06em;
  line-height:.94;margin:.45rem 0 .65rem;color:var(--ink);text-wrap:balance;
  text-shadow:0 0 30px rgba(255,79,216,.12)
}
.hero p{max-width:690px;color:#ddd6ee;font-size:1.03rem;line-height:1.55;margin-bottom:.3rem}
.hero-kicker{
  display:inline-block;font-size:.79rem;font-weight:850;letter-spacing:.08em;text-transform:uppercase;
  color:var(--cyan);margin-top:.75rem
}
.future-marquee{
  margin-top:9px;padding-top:8px;border-top:1px dashed rgba(255,255,255,.18);
  font-size:.72rem;font-weight:850;letter-spacing:.15em;text-transform:uppercase;color:rgba(255,249,235,.66)
}
.future-marquee span{color:var(--pink)}

.flowbox{
  background:linear-gradient(145deg,rgba(23,21,47,.96),rgba(17,15,37,.96));
  border:1px solid rgba(103,232,249,.19);border-radius:20px;padding:12px;margin:4px 0 10px;
  box-shadow:0 16px 45px rgba(0,0,0,.18)
}
.flowbox strong{color:var(--gold);letter-spacing:.03em}
.section-title{font-size:1.38rem;font-weight:900;letter-spacing:-.035em;margin:20px 0 8px;color:var(--ink)}
.result-summary{color:var(--muted);margin:.35rem 0 1rem}

.event-card{
  position:relative;overflow:hidden;
  background:linear-gradient(145deg,rgba(27,25,54,.97),rgba(18,16,39,.98));
  border:1px solid rgba(255,255,255,.14);border-radius:20px;padding:15px;margin-bottom:8px;
  min-height:164px;box-shadow:0 12px 28px rgba(0,0,0,.2);
  transition:transform .18s ease,border-color .18s ease,box-shadow .18s ease
}
.event-card::before{
  content:"";position:absolute;left:0;right:0;top:0;height:3px;
  background:linear-gradient(90deg,var(--pink),var(--violet),var(--cyan),var(--lime))
}
.event-card::after{
  content:"";position:absolute;width:72px;height:72px;right:-36px;bottom:-36px;border-radius:50%;
  border:1px dashed rgba(255,215,106,.28)
}
.event-card:hover{
  transform:translateY(-2px);border-color:rgba(103,232,249,.38);
  box-shadow:0 18px 45px rgba(0,0,0,.3),0 0 26px rgba(103,232,249,.06)
}
.event-topline{display:flex;gap:8px;align-items:center;justify-content:space-between;margin-bottom:9px}
.event-kind{font-size:.7rem;font-weight:900;letter-spacing:.1em;text-transform:uppercase;color:var(--cyan)}
.event-flags{display:flex;gap:5px;flex-wrap:wrap;justify-content:flex-end}
.badge{
  display:inline-block;background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.1);
  border-radius:999px;padding:4px 8px;font-size:.65rem;font-weight:900;color:var(--ink)
}
.badge-new{background:var(--pink);color:#160b20;border-color:transparent;box-shadow:0 0 16px rgba(255,79,216,.22)}
.badge-free{background:var(--lime);color:#12160a;border-color:transparent}
.badge-dates{background:rgba(167,139,250,.16);color:#ddd2ff;border-color:rgba(167,139,250,.32)}
.badge-warn{background:var(--gold);color:#211704;border-color:transparent}

.badge-time{
  background:rgba(103,232,249,.13);color:#aef5ff;border-color:rgba(103,232,249,.25)
}
.badge-time-now{
  background:var(--pink);color:#170b1e;border-color:transparent;
  box-shadow:0 0 18px rgba(255,79,216,.22)
}
.badge-time-soon{
  background:var(--gold);color:#201604;border-color:transparent
}
.event-title{font-size:1.18rem;font-weight:900;letter-spacing:-.025em;margin:0 0 10px;line-height:1.2;color:var(--ink);min-height:2.45em;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.quick-facts{display:grid;gap:5px}
.quick-fact{display:flex;align-items:flex-start;gap:8px;color:#d5cfe3;font-size:.9rem;line-height:1.3}
.fact-icon{width:1.05rem;flex:0 0 1.05rem;text-align:center;color:var(--gold)}
.fact-price{font-weight:900;color:var(--lime)}
.why{margin-top:.75rem;font-size:.8rem;font-weight:750;color:#b9f4fa}

.inline-detail{
  background:rgba(255,255,255,.035);border:1px solid rgba(255,255,255,.08);
  border-radius:18px;padding:13px 14px;margin:2px 0 9px;
  font-size:.88rem;line-height:1.55;color:#d8d2e7
}
.alternate-dates{margin:.65rem 0 0;padding:.6rem .7rem;border-left:2px solid rgba(167,139,250,.55);color:#ddd2ff}
.inline-detail p{margin:.7rem 0 0}.detail-trust{font-size:.75rem;color:#928aa9}
.detail-box{background:var(--panel);border:1px solid var(--line);border-radius:20px;padding:22px;margin-top:12px}

/* Streamlit controls: futuristic but readable */
div[data-testid="stButton"] button,
div[data-testid="stLinkButton"] a{
  border-radius:999px;min-height:32px;font-weight:850;
  border:1px solid rgba(103,232,249,.26)!important;
  background:linear-gradient(135deg,rgba(28,25,58,.96),rgba(20,18,44,.96))!important;
  color:var(--ink)!important
}
div[data-testid="stButton"] button:hover,
div[data-testid="stLinkButton"] a:hover{
  border-color:var(--cyan)!important;box-shadow:0 0 22px rgba(103,232,249,.13)!important
}
div[data-baseweb="select"]>div,
div[data-baseweb="input"]>div,
div[data-baseweb="base-input"],
textarea{
  background:rgba(255,255,255,.055)!important;
  border-color:rgba(255,255,255,.14)!important;
  color:var(--ink)!important
}
[data-testid="stExpander"]{
  border:1px solid rgba(255,255,255,.11)!important;border-radius:18px!important;
  background:rgba(255,255,255,.025)!important
}
[data-testid="stMetric"]{
  background:rgba(255,255,255,.035);border:1px solid rgba(255,255,255,.08);
  border-radius:18px;padding:10px 12px
}
[data-testid="stDataFrame"]{border-radius:18px;overflow:hidden}
[data-testid="stRadio"]>div{
  background:rgba(18,16,39,.86);border:1px solid rgba(255,255,255,.1);
  padding:5px 8px;border-radius:999px;width:max-content
}
label,p,.stCaption{color:var(--muted)}
h1,h2,h3,h4{color:var(--ink)}

.admin-note{
  border-left:3px solid var(--cyan);padding:8px 12px;background:rgba(103,232,249,.05);
  border-radius:0 12px 12px 0;color:var(--muted);font-size:.82rem
}


.poster-sigil{
  position:absolute;right:14px;top:44px;width:42px;height:42px;border-radius:14px;
  display:flex;align-items:center;justify-content:center;font-size:1.35rem;font-weight:900;
  border:1px solid rgba(255,255,255,.13);background:rgba(255,255,255,.055);
  transform:rotate(5deg);box-shadow:0 8px 18px rgba(0,0,0,.14)
}
.event-card .event-title{padding-right:44px}
.theme-music{--poster-a:#ff4fd8;--poster-b:#8b5cf6}
.theme-sport{--poster-a:#67e8f9;--poster-b:#d9ff67}
.theme-family{--poster-a:#ffd76a;--poster-b:#ff8ccf}
.theme-stage{--poster-a:#a78bfa;--poster-b:#ff4fd8}
.theme-market{--poster-a:#ffd76a;--poster-b:#67e8f9}
.theme-food{--poster-a:#ff9f68;--poster-b:#ffd76a}
.theme-other{--poster-a:#8b5cf6;--poster-b:#67e8f9}
.event-card[class*="theme-"]::before{
  background:linear-gradient(90deg,var(--poster-a),var(--poster-b))
}
.event-card[class*="theme-"] .poster-sigil{
  color:var(--poster-a);border-color:color-mix(in srgb,var(--poster-a) 42%,transparent);
  box-shadow:0 0 22px color-mix(in srgb,var(--poster-a) 15%,transparent)
}
.event-card[class*="theme-"] .event-kind{color:var(--poster-b)}
.event-card[class*="theme-"] .fact-icon{color:var(--poster-a)}
.event-card[class*="theme-"]:hover{
  border-color:color-mix(in srgb,var(--poster-b) 38%,transparent)
}


.zone-chip{
  display:inline-flex;align-items:center;gap:6px;
  margin:0;padding:4px 8px;border-radius:999px;
  font-size:.6rem;font-weight:900;letter-spacing:.11em;text-transform:uppercase;
  color:#100d21;background:var(--poster-b);
  box-shadow:0 0 16px color-mix(in srgb,var(--poster-b) 18%,transparent)
}
.festival-districts{display:none}
.festival-district{
  border:1px solid rgba(255,255,255,.1);background:rgba(255,255,255,.035);
  border-radius:14px;padding:7px 10px;min-height:48px
}
.festival-district b{display:block;color:var(--ink);font-size:.82rem;letter-spacing:.03em;margin-bottom:4px}
.festival-district span{display:none}


.nightline{
  display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin:0 0 8px;
  padding:0;border:0;background:transparent
}
.nightline-label{
  font-size:.64rem;font-weight:900;letter-spacing:.14em;text-transform:uppercase;
  color:var(--pink);margin-right:2px
}
.nightline-help{font-size:.72rem;color:var(--muted);margin:2px 0 8px}


.tonight-mode{
  margin:4px 0 18px;padding:16px;border-radius:24px;
  background:
    radial-gradient(circle at 90% 10%,rgba(255,79,216,.18),transparent 35%),
    linear-gradient(135deg,rgba(20,18,46,.98),rgba(12,10,29,.98));
  border:1px solid rgba(255,79,216,.22)
}
.tonight-mode-head{
  display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:10px
}
.tonight-mode-title{font-size:1.05rem;font-weight:950;letter-spacing:-.02em;color:var(--ink)}
.tonight-mode-kicker{font-size:.64rem;font-weight:900;letter-spacing:.13em;text-transform:uppercase;color:var(--pink)}
.tonight-mode-copy{font-size:.78rem;color:var(--muted);margin-bottom:12px}
.tonight-pick-label{
  display:inline-flex;margin:0 0 6px;padding:4px 8px;border-radius:999px;
  background:var(--pink);color:#170b1e;font-size:.62rem;font-weight:950;letter-spacing:.08em;text-transform:uppercase
}
.tonight-summary{font-size:.75rem;color:#d9d3e7;margin:-3px 0 8px}


.last-minute-shell{
  margin:4px 0 18px;padding:16px;border-radius:24px;
  background:
    radial-gradient(circle at 88% 8%,rgba(217,255,103,.16),transparent 34%),
    linear-gradient(135deg,rgba(19,29,29,.98),rgba(10,17,28,.98));
  border:1px solid rgba(217,255,103,.2)
}
.last-minute-head{
  display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:8px
}
.last-minute-title{font-size:1.05rem;font-weight:950;color:var(--ink)}
.last-minute-kicker{font-size:.64rem;font-weight:900;letter-spacing:.13em;text-transform:uppercase;color:var(--lime)}
.last-minute-copy{font-size:.78rem;color:var(--muted)}
.last-minute-label{
  display:inline-flex;margin:0 0 6px;padding:4px 8px;border-radius:999px;
  background:var(--lime);color:#0f1505;font-size:.62rem;font-weight:950;letter-spacing:.08em;text-transform:uppercase
}
.last-minute-meta{font-size:.75rem;color:#dcebc7;margin:-2px 0 8px}


.go-now-shell{
  margin:4px 0 18px;padding:16px;border-radius:24px;
  background:
    radial-gradient(circle at 88% 10%,rgba(103,232,249,.17),transparent 34%),
    linear-gradient(135deg,rgba(11,29,35,.98),rgba(11,16,30,.98));
  border:1px solid rgba(103,232,249,.22)
}
.go-now-head{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:8px}
.go-now-title{font-size:1.05rem;font-weight:950;color:var(--ink)}
.go-now-kicker{font-size:.64rem;font-weight:900;letter-spacing:.13em;text-transform:uppercase;color:var(--cyan)}
.go-now-copy{font-size:.78rem;color:var(--muted)}
.go-now-label{
  display:inline-flex;margin:0 0 6px;padding:4px 8px;border-radius:999px;
  background:var(--cyan);color:#071419;font-size:.62rem;font-weight:950;letter-spacing:.08em;text-transform:uppercase
}
.go-now-meta{font-size:.75rem;color:#d6f7fb;margin:-2px 0 8px}

@media(max-width:1100px) and (min-width:801px){
  .festival-districts{grid-template-columns:repeat(3,1fr)}
}

@media(max-width:800px){
  .block-container{padding-left:.75rem;padding-right:.75rem}
  .hero{padding:17px 16px 15px;border-radius:22px}
  .hero h1{font-size:2.35rem;max-width:100%}
  .hero::before{width:220px;height:220px;right:-100px;top:-100px}
  .hero::after{display:none}
  .future-marquee{font-size:.62rem;letter-spacing:.08em}
  .flowbox{padding:11px;border-radius:18px}
  .event-card{min-height:auto;padding:15px;border-radius:21px}
  .event-title{font-size:1.13rem;padding-right:42px}.quick-fact{font-size:.89rem}.source{white-space:normal}
  .poster-sigil{width:36px;height:36px;right:11px;top:42px;font-size:1.1rem;border-radius:12px}
  .section-title{font-size:1.28rem}
  .festival-districts{grid-template-columns:repeat(2,1fr);gap:8px}
  .festival-district{min-height:auto;padding:10px 11px}
  .tonight-mode{padding:13px;border-radius:20px}.tonight-mode-head{align-items:flex-start;flex-direction:column;gap:2px}
  .last-minute-shell{padding:13px;border-radius:20px}.last-minute-head{align-items:flex-start;flex-direction:column;gap:2px}
  .go-now-shell{padding:13px;border-radius:20px}.go-now-head{align-items:flex-start;flex-direction:column;gap:2px}
}
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
redirect_secret = str(secret("UPPLEVIO_REDIRECT_SECRET") or "").strip()
public_base_url = str(secret("UPPLEVIO_PUBLIC_URL") or "").strip()

# Redirect mode is handled before event imports so a booking click is not delayed by source fetching.
_redirect_token = st.query_params.get("go")
if _redirect_token:
    try:
        _redirect = process_redirect(str(_redirect_token), secret=redirect_secret)
        _seen_redirects = st.session_state.setdefault("recorded_redirects", set())
        if _redirect.click_id not in _seen_redirects:
            record_action(
                "booking_outbound",
                event_id=_redirect.event_id,
                campaign_id=_redirect.campaign_id,
                partner=_redirect.partner_name,
                context={"click_id": _redirect.click_id, "tracked_redirect": True},
            )
            _seen_redirects.add(_redirect.click_id)
        st.markdown("### Skickar dig vidare till bokningen…")
        st.caption(f"Bokningspartner: {_redirect.partner_name}")
        st.link_button("Fortsätt till bokningen", _redirect.destination_url, use_container_width=True)
        _js_url = __import__("json").dumps(_redirect.destination_url)
        components.html("<script>window.top.location.replace(" + _js_url + ");</script>", height=0)
    except Exception:
        st.error("Bokningslänken kunde inte verifieras eller har gått ut.")
        st.caption("Gå tillbaka till Upplevio och öppna aktiviteten igen. Ingen osäker omdirigering genomfördes.")
    st.stop()

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
def cached_load_events(api_key_value, official_keys, collector_source_keys, entertainment_source_keys, include_demo_value, source_cache_version):
    # Invalidate transitive source changes immediately on deploy. Streamlit hashes
    # this wrapper, but cannot see that an imported source adapter changed.
    del source_cache_version
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
        APP_VERSION,
    )

@st.cache_data(ttl=900, show_spinner=False)
def cached_prepare_events(raw_event_list, source_health_value):
    prepared_events, prepared_review_pairs = deduplicate(raw_event_list)
    apply_booking_partner_attribution(prepared_events)
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



def event_visual_theme(e):
    _tags = getattr(e, "tags", None) or []
    if isinstance(_tags, str):
        _tags = [_tags]
    text = f"{getattr(e,'event_type','')} {getattr(e,'category','')} {' '.join(_tags)}".casefold()
    if any(k in text for k in ["konsert","musik","festival","rock","jazz","pop","live"]):
        return {"class":"theme-music","icon":"♫","label":"MUSIK"}
    if any(k in text for k in ["sport","fotboll","hockey","match","innebandy"]):
        return {"class":"theme-sport","icon":"⚡","label":"SPORT"}
    if any(k in text for k in ["familj","barn","lov","kids"]):
        return {"class":"theme-family","icon":"✦","label":"FAMILJ"}
    if any(k in text for k in ["teater","scen","show","dans","musikal","föreställning"]):
        return {"class":"theme-stage","icon":"◐","label":"SCEN"}
    if any(k in text for k in ["marknad","mässa","expo","loppis"]):
        return {"class":"theme-market","icon":"◇","label":"MARKNAD"}
    if any(k in text for k in ["mat","dryck","vin","öl","food"]):
        return {"class":"theme-food","icon":"✺","label":"MAT & DRYCK"}
    return {"class":"theme-other","icon":"✧","label":"UPPLEVELSE"}



def event_festival_zone(e):
    theme = event_visual_theme(e)["class"]
    mapping = {
        "theme-music": ("MAIN STAGE", "♫"),
        "theme-sport": ("ARENA", "⚡"),
        "theme-family": ("FAMILY ZONE", "✦"),
        "theme-stage": ("SHOW TENT", "◐"),
        "theme-market": ("NIGHT MARKET", "◇"),
        "theme-food": ("FOOD DISTRICT", "✺"),
        "theme-other": ("HIDDEN GEMS", "✧"),
    }
    return mapping.get(theme, ("HIDDEN GEMS", "✧"))



def nightline_matches(e, preset, *, distance_km=None):
    if not preset:
        return True
    if preset == "Go Now":
        return go_now_match(e, distance_km=distance_km)
    if preset == "Last Minute":
        return last_minute_match(e)
    if preset == "Ikväll":
        return evening_match(e)
    if preset == "Hidden Gems":
        return event_festival_zone(e)[0] == "HIDDEN GEMS" or is_local_discovery_tip(e)
    if preset == "För familjen":
        return event_festival_zone(e)[0] == "FAMILY ZONE"
    return True


def card_markup(e, origin_city=None, rank_reasons=None):
    theme = event_visual_theme(e)
    zone_name, zone_icon = event_festival_zone(e)
    flags = []
    if getattr(e, "is_sponsored", False):
        flags.append('<span class="badge">SPONSRAD</span>')
    alternate_dates = getattr(e, "_alternate_dates", []) or []
    _showtime = showtime_status(e)
    if _showtime:
        _time_class = "badge-time-now" if _showtime.key == "now" else ("badge-time-soon" if _showtime.key == "soon" else "badge-time")
        flags.append(f'<span class="badge {_time_class}">{safe(_showtime.label.upper())}</span>')
    warning = status_label(e)
    if warning:
        flags.append(f'<span class="badge badge-warn">{safe(warning.upper())}</span>')
    if e.price_status == "free":
        flags.append('<span class="badge badge-free">GRATIS</span>')
    if alternate_dates:
        flags.append(f'<span class="badge badge-dates">+{len(alternate_dates)} DATUM</span>')
    if is_new(e):
        flags.append('<span class="badge badge-new">NY</span>')
    if is_local_discovery_tip(e):
        flags.append('<span class="badge">LOKALT TIPS</span>')
    flags = flags[:2]
    dist, geo_confidence = distance_info(e, origin_city) if origin_city and origin_city != "Hela Sverige" else (None, "unknown")
    date_text = compact_date_label(e, today)
    place_text = compact_location_label(e, dist, approximate=(geo_confidence == "city"))
    why_text = ""
    if rank_reasons:
        generic_reasons = {
            "mycket nära", "nära", "rimligt nära", "inom vald radie",
            "händer idag", "händer snart", "den närmaste veckan",
            "inom två veckor", "inom en månad",
        }
        distinctive = [reason for reason in rank_reasons if reason not in generic_reasons]
        if distinctive:
            why_text = f'<div class="why">Varför: {safe(distinctive[0])}</div>'
    return f"""<div class="event-card {theme['class']}">
    <div class="poster-sigil">{safe(theme['icon'])}</div>
    <div class="event-topline"><div class="zone-chip">{safe(zone_icon)} {safe(zone_name)}</div><div class="event-flags">{''.join(flags)}</div></div>
    <div class="event-title">{safe(e.title)}</div>
    <div class="quick-facts">
      <div class="quick-fact"><span class="fact-icon">◷</span><span><b>{safe(date_text)}</b></span></div>
      <div class="quick-fact"><span class="fact-icon">⌖</span><span>{safe(place_text)}</span></div>
      <div class="quick-fact"><span class="fact-icon">◉</span><span class="fact-price">{safe(price_label(e))}</span></div>
    </div>
    {why_text}</div>"""


def render_inline_details(e):
    date_text = compact_date_label(e, today)
    alternate_events = getattr(e, "_alternate_events", []) or []
    alternate_dates_markup = ""
    if alternate_events:
        alternate_labels = [compact_date_label(item, today) for item in alternate_events]
        alternate_dates_markup = (
            '<div class="alternate-dates"><b>Fler datum</b><br>'
            + "<br>".join(safe(label) for label in alternate_labels)
            + "</div>"
        )
    st.markdown(
        f"""<div class="inline-detail"><b>{safe(date_text)}</b><br>
        {safe(e.venue or "Plats ej angiven")}{safe((", " + e.city) if e.city else "")}<br>
        <b>{safe(price_label(e))}</b><br>
        {f'<span>🚪 Dörrar/insläpp {safe(e.door_time)}</span><br>' if getattr(e, "door_time", None) else ''}
        {f'<span>◌ Åldersgräns: {safe(e.age_limit)}</span><br>' if getattr(e, "age_limit", None) else ''}
        <span class="detail-trust">{safe(verification_label(e))} · {safe(", ".join(e.source_names))}</span>
        {alternate_dates_markup}
        {f'<p>{safe(e.description)}</p>' if e.description else ''}</div>""",
        unsafe_allow_html=True,
    )
    cta = booking_cta(e)
    info_url = primary_info_target(e)
    if cta:
        _cta_url = cta.url
        if cta.track_as_booking:
            _cta_url = build_tracked_url(
                event=e, destination_url=cta.url, public_base_url=public_base_url, secret=redirect_secret
            )
        st.link_button(cta.label, _cta_url, use_container_width=True)
    if info_url and (not cta or info_url != cta.url):
        st.link_button("Officiell sida", info_url, use_container_width=True)


def render_measured_details(e, *, surface: str):
    state_key = f"details-open-{surface}-{e.id}"
    is_open = bool(st.session_state.get(state_key, False))
    label = "Dölj detaljer" if is_open else "Detaljer"
    if st.button(label, key=f"details-btn-{surface}-{e.id}", use_container_width=True):
        new_state = not is_open
        st.session_state[state_key] = new_state
        if new_state:
            record_action(
                "activity_open",
                event_id=e.id,
                partner=getattr(e, "booking_partner", None),
                context={
                    "source": ", ".join(e.source_names or []) or "Okänd källa",
                    "event_type": e.event_type or "Okänd typ",
                    "surface": surface,
                },
            )
        st.rerun()
    if st.session_state.get(state_key, False):
        render_inline_details(e)


def render_card_actions(e, *, surface: str):
    """Compact action row: details and save share one row under the card."""
    state_key = f"details-open-{surface}-{e.id}"
    is_open = bool(st.session_state.get(state_key, False))
    detail_label = "Dölj" if is_open else "Detaljer"
    a1, a2 = st.columns([4, 1])
    with a1:
        if st.button(detail_label, key=f"details-btn-{surface}-{e.id}", use_container_width=True):
            new_state = not is_open
            st.session_state[state_key] = new_state
            if new_state:
                record_action(
                    "activity_open", event_id=e.id, partner=getattr(e, "booking_partner", None),
                    context={
                        "source": ", ".join(e.source_names or []) or "Okänd källa",
                        "event_type": e.event_type or "Okänd typ", "surface": surface,
                    },
                )
            st.rerun()
    with a2:
        save_label = "♥" if e.id in fav_ids else "♡"
        save_help = "Ta bort från sparat" if e.id in fav_ids else "Spara event"
        if st.button(save_label, key=f"save-{surface}-{e.id}", use_container_width=True, help=save_help):
            toggle_favorite(e.id)
            st.rerun()
    if st.session_state.get(state_key, False):
        render_inline_details(e)


future_events = [e for e in events if date.fromisoformat(e.end_date or e.start_date) >= today and not e.is_demo and not is_high_confidence_noise(e)]
fav_ids = favorite_ids()

st.markdown(
    """<div class="hero">
<div class="eyebrow">UPPLEVIO · FUTURE CARNIVAL</div>
<h1>Hitta det du inte vill missa.</h1>
<p>Din portal till konserter, matcher, marknader, scener, familjeäventyr och märkligt bra saker som händer nära dig.</p>
<div class="hero-kicker">Välj plats + tid · Upplevio tänder resten</div>
<div class="future-marquee">LIVE NU <span>✦</span> LOKALT <span>✦</span> OVÄNTAT <span>✦</span> NÄSTA UPPLEVELSE</div>
</div>""",
    unsafe_allow_html=True,
)

active_view = st.radio(
    "Vy", ["Upptäck", "Sparat", "Admin"], horizontal=True, label_visibility="collapsed", key="active_view"
)

if active_view == "Upptäck":
    if health_summary["has_public_warning"]:
        st.warning("Resultaten kan vara ofullständiga just nu. Någon datakälla behöver kontrolleras.")
    st.markdown('<div class="nightline"><span class="nightline-label">SNABBVAL</span></div>', unsafe_allow_html=True)
    q1, q2, q3, q4 = st.columns(4)
    _quick_buttons = [
        (q1, "Nu & snart", "Go Now"),
        (q2, "Ikväll", "Ikväll"),
        (q3, "I helgen", "I helgen"),
        (q4, "Gratis", "Gratis"),
    ]
    for _col, _label, _preset in _quick_buttons:
        with _col:
            if st.button(_label, key=f"nightline-{_preset}", use_container_width=True):
                st.session_state["nightline_preset"] = _preset
                if _preset == "Go Now":
                    st.session_state["discover_when"] = "Idag"
                    if st.session_state.get("discover_city", DISCOVERY_DEFAULTS["city"]) == "Hela Sverige":
                        st.session_state["discover_city"] = DISCOVERY_DEFAULTS["city"]
                    st.session_state["discover_radius"] = 50
                elif _preset == "Last Minute":
                    st.session_state["discover_when"] = "Idag"
                elif _preset == "Ikväll":
                    st.session_state["discover_when"] = "Idag"
                elif _preset == "I helgen":
                    st.session_state["discover_when"] = "I helgen"
                elif _preset == "Gratis":
                    st.session_state["discover_price"] = "Gratis"
                elif _preset == "Nära vald stad":
                    if st.session_state.get("discover_city", DISCOVERY_DEFAULTS["city"]) == "Hela Sverige":
                        st.session_state["discover_city"] = DISCOVERY_DEFAULTS["city"]
                    st.session_state["discover_radius"] = 25
                st.rerun()
    _active_preset = st.session_state.get("nightline_preset")
    if _active_preset:
        if _active_preset == "Go Now":
            _preset_note = " · nära event med rimlig tid till start."
        elif _active_preset == "Ikväll":
            _preset_note = " · event med verifierad starttid senare idag."
        else:
            _preset_note = ""
        st.markdown(f'<div class="nightline-help">Aktivt: <b>{safe(_active_preset)}</b>{safe(_preset_note)}</div>', unsafe_allow_html=True)

    city_choices = ["Hela Sverige"] + sorted(CITY_COORDS.keys())
    default_city = DISCOVERY_DEFAULTS["city"]
    if "discover_city" not in st.session_state:
        st.session_state["discover_city"] = default_city if default_city in city_choices else city_choices[0]
    r1c1, r1c2, r1c3, r1c4 = st.columns(4)
    with r1c1:
        origin_city = st.selectbox("📍 Var?", city_choices, key="discover_city")
    with r1c2:
        when_choices = ["Idag", "I helgen", "Nästa 7 dagar", "Nästa 30 dagar", "Nästa 3 månader"]
        if "discover_when" not in st.session_state:
            st.session_state["discover_when"] = DISCOVERY_DEFAULTS["when"]
        when = st.selectbox("📅 När?", when_choices, key="discover_when")

    with r1c3:
        radius_choices = [25, 50, 100, 200, 300]
        if "discover_radius" not in st.session_state:
            st.session_state["discover_radius"] = DISCOVERY_DEFAULTS["radius_km"]
        radius_km = st.selectbox("🚗 Hur långt?", radius_choices, key="discover_radius", disabled=(origin_city == "Hela Sverige"))
    with r1c4:
        price_choices = ["Alla priser", "Gratis", "Max 100 kr", "Max 250 kr", "Max 500 kr"]
        if "discover_price" not in st.session_state:
            st.session_state["discover_price"] = DISCOVERY_DEFAULTS["price"]
        price_filter = st.selectbox("💰 Budget?", price_choices, key="discover_price")

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
        if st.session_state.get("nightline_preset") and st.button("Rensa snabbval", key="clear-nightline"):
            st.session_state["nightline_preset"] = None
            st.rerun()
    def matches(e):
        d = event_dt(e)
        _preset = st.session_state.get("nightline_preset")
        _preset_distance = distance_from_city(e, origin_city) if origin_city != "Hela Sverige" else None
        if not nightline_matches(e, _preset, distance_km=_preset_distance):
            return False
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
    rank_reasons = {e.id: rank.reasons for rank, e in ranked_results}
    # Discovery shows one card per production. Repeated performances remain separate in the
    # underlying event model and can still be inspected via source/admin diagnostics.
    filtered = collapse_productions([e for _, e in ranked_results])

    context_text = discovery_context_label(origin_city, when, None if origin_city == "Hela Sverige" else radius_km, price_filter)
    st.markdown(f'<div class="result-summary"><b>{len(filtered)}</b> event · {safe(context_text)}</div>', unsafe_allow_html=True)
    if type_filter == "Sport" and origin_city == "Örebro":
        st.caption("Sport bevakas från officiella klubbkällor för fotboll, ishockey, basket, handboll, volleyboll, innebandy och amerikansk fotboll. Mindre serier och ungdomslag kan fortfarande saknas.")

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
                cols = st.columns(min(2, len(fresh_events)))
                for i, e in enumerate(fresh_events):
                    shown_fallback_ids.add(e.id)
                    with cols[i % len(cols)]:
                        st.markdown(card_markup(e, origin_city), unsafe_allow_html=True)
        else:
            st.caption("Upplevio hittar inga nära alternativ utan att ändra sökningen mer än rimligt. Prova att ta bort sökord eller eventtyp om du vill bredda ytterligare.")
    else:
        st.markdown('<div class="section-title">✦ På scen för dig</div>', unsafe_allow_html=True)
        st.caption("En produktion per kort. Fler föreställningsdatum samlas på samma kort; NY och GRATIS markeras direkt.")
        filter_signature = result_filter_signature(
            origin_city=origin_city, when=when, radius_km=None if origin_city == "Hela Sverige" else radius_km,
            price_filter=price_filter, query=query, type_filter=type_filter, only_new=only_new, interests=interests,
        )
        if st.session_state.get("result_filter_signature") != filter_signature:
            st.session_state["result_filter_signature"] = filter_signature
            st.session_state["result_limit"] = INITIAL_RESULT_LIMIT

        _go_now_active = st.session_state.get("nightline_preset") == "Go Now"
        _go_now_picks = go_now_shortlist(
            filtered,
            distance_lookup=lambda event: distance_from_city(event, origin_city) if origin_city != "Hela Sverige" else None,
            limit=3,
        ) if _go_now_active else []
        _after_go_now = go_now_remaining(filtered, _go_now_picks) if _go_now_active else filtered

        _last_minute_active = st.session_state.get("nightline_preset") == "Last Minute"
        _last_minute_picks = last_minute_shortlist(_after_go_now, limit=3) if _last_minute_active else []
        _after_last_minute = last_minute_remaining(_after_go_now, _last_minute_picks) if _last_minute_active else _after_go_now

        _tonight_active = st.session_state.get("nightline_preset") == "Ikväll"
        _tonight_picks = tonight_shortlist(_after_last_minute, 3) if _tonight_active else []
        _main_pool = tonight_remaining(_after_last_minute, _tonight_picks) if _tonight_active else _after_last_minute

        if _go_now_active and _go_now_picks:
            st.markdown(
                """<div class="go-now-shell">
                <div class="go-now-head">
                  <div class="go-now-title">➜ Go Now</div>
                  <div class="go-now-kicker">TID + AVSTÅND · INTE RESTIDSLOFTE</div>
                </div>
                <div class="go-now-copy">Nära event med tillräcklig planeringsmarginal. Kontrollera alltid faktisk restid innan du åker.</div>
                </div>""",
                unsafe_allow_html=True,
            )
            _gn_cols = st.columns(min(2, len(_go_now_picks)))
            for _idx, _e in enumerate(_go_now_picks):
                with _gn_cols[_idx % len(_gn_cols)]:
                    _dist = distance_from_city(_e, origin_city) if origin_city != "Hela Sverige" else None
                    _info = go_now_info(_e, distance_km=_dist)
                    _cta = booking_cta(_e)
                    _parts = []
                    if _info:
                        _parts.extend([f"{_info.minutes_to_start} min till start", f"{_info.distance_km:g} km", _info.planning_note])
                    _parts.append(price_label(_e))
                    if _cta and _cta.track_as_booking:
                        _parts.append("Bokningslänk finns")
                    st.markdown('<div class="go-now-label">GO NOW</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="go-now-meta">{safe(" · ".join([x for x in _parts if x]))}</div>', unsafe_allow_html=True)
                    st.markdown(card_markup(_e, origin_city, rank_reasons.get(_e.id)), unsafe_allow_html=True)
                    render_card_actions(_e, surface="go_now")
            if _main_pool:
                st.markdown('<div class="section-title">Fler möjliga att planera nu</div>', unsafe_allow_html=True)

        if _last_minute_active and _last_minute_picks:
            st.markdown(
                """<div class="last-minute-shell">
                <div class="last-minute-head">
                  <div class="last-minute-title">⚡ Last Minute</div>
                  <div class="last-minute-kicker">30–180 MIN · SÄKER STARTTID</div>
                </div>
                <div class="last-minute-copy">Event som börjar snart. Ordningen följer samma discovery-ranking som vanligt.</div>
                </div>""",
                unsafe_allow_html=True,
            )
            _lm_cols = st.columns(min(2, len(_last_minute_picks)))
            for _idx, _e in enumerate(_last_minute_picks):
                with _lm_cols[_idx % len(_lm_cols)]:
                    _info = last_minute_info(_e)
                    _dist = distance_from_city(_e, origin_city) if origin_city != "Hela Sverige" else None
                    _cta = booking_cta(_e)
                    _parts = [_info.urgency_label if _info else ""]
                    if _dist is not None:
                        _parts.append(f"{_dist:g} km")
                    _parts.append(price_label(_e))
                    if _cta and _cta.track_as_booking:
                        _parts.append("Bokningslänk finns")
                    st.markdown('<div class="last-minute-label">LAST MINUTE</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="last-minute-meta">{safe(" · ".join([x for x in _parts if x]))}</div>', unsafe_allow_html=True)
                    st.markdown(card_markup(_e, origin_city, rank_reasons.get(_e.id)), unsafe_allow_html=True)
                    render_card_actions(_e, surface="last_minute")
            if _main_pool:
                st.markdown('<div class="section-title">Fler som börjar snart</div>', unsafe_allow_html=True)

        if _tonight_active and _tonight_picks:
            st.markdown(
                """<div class="tonight-mode">
                <div class="tonight-mode-head">
                  <div class="tonight-mode-title">🌙 Vad ska jag göra ikväll?</div>
                  <div class="tonight-mode-kicker">TOPP 3 · SAMMA DISCOVERY-RANKING</div>
                </div>
                <div class="tonight-mode-copy">Tre snabbaste besluten först. Resten av kvällens event finns direkt under.</div>
                </div>""",
                unsafe_allow_html=True,
            )
            _pick_cols = st.columns(min(2, len(_tonight_picks)))
            for _idx, _pick in enumerate(_tonight_picks):
                _e = _pick.event
                with _pick_cols[_idx % len(_pick_cols)]:
                    _dist = distance_from_city(_e, origin_city) if origin_city != "Hela Sverige" else None
                    _summary = tonight_summary(_e, distance=_dist, price_text=price_label(_e))
                    st.markdown(f'<div class="tonight-pick-label">{safe(_pick.label)}</div>', unsafe_allow_html=True)
                    if _summary:
                        st.markdown(f'<div class="tonight-summary">{safe(_summary)}</div>', unsafe_allow_html=True)
                    st.markdown(card_markup(_e, origin_city, rank_reasons.get(_e.id)), unsafe_allow_html=True)
                    render_card_actions(_e, surface="tonight")
            if _main_pool:
                st.markdown('<div class="section-title">Fler ikväll</div>', unsafe_allow_html=True)

        visible_count = clamp_result_limit(len(_main_pool), st.session_state.get("result_limit"))
        visible_events = _main_pool[:visible_count]
        _impression_events = _go_now_picks + _last_minute_picks + [pick.event for pick in _tonight_picks] + visible_events
        _seen_impressions = st.session_state.setdefault("seen_impressions", set())
        for _e in _impression_events:
            _imp_key = session_impression_key(_e.id, filter_signature)
            if _imp_key not in _seen_impressions:
                record_action(
                    "impression",
                    event_id=_e.id,
                    partner=getattr(_e, "booking_partner", None),
                    context={
                        "source": ", ".join(_e.source_names or []) or "Okänd källa",
                        "event_type": _e.event_type or "Okänd typ",
                        "surface": (
                            "go_now" if _go_now_active and any(x.id == _e.id for x in _go_now_picks)
                            else ("last_minute" if _last_minute_active and any(x.id == _e.id for x in _last_minute_picks)
                            else ("tonight" if _tonight_active and any(p.event.id == _e.id for p in _tonight_picks) else "discover"))
                        ),
                        "filter_signature": filter_signature,
                    },
                )
                _seen_impressions.add(_imp_key)
        cols = st.columns(2)
        for i, e in enumerate(visible_events):
            with cols[i % len(cols)]:
                st.markdown(card_markup(e, origin_city, rank_reasons.get(e.id)), unsafe_allow_html=True)
                render_card_actions(e, surface="discover")

        remaining = remaining_result_count(len(_main_pool), visible_count)
        if remaining:
            next_batch = min(RESULT_BATCH_SIZE, remaining)
            if st.button(f"Visa {next_batch} till · {remaining} kvar", key="show-more-results", use_container_width=True):
                st.session_state["result_limit"] = next_result_limit(len(_main_pool), visible_count)
                st.rerun()

elif active_view == "Sparat":
    saved = sorted([e for e in future_events if e.id in fav_ids], key=event_dt)
    st.markdown('<div class="section-title">Sparade event</div>', unsafe_allow_html=True)
    if not saved:
        st.info("Du har inte sparat några event ännu.")
    else:
        cols = st.columns(2)
        for i, e in enumerate(saved):
            with cols[i % len(cols)]:
                st.markdown(card_markup(e), unsafe_allow_html=True)
                render_card_actions(e, surface="saved")

elif active_view == "Admin":
    st.markdown('<div class="admin-note">Kontrollrum · datakvalitet, källor och teknisk diagnostik. Den här informationen påverkar inte den vanliga användarresan.</div>', unsafe_allow_html=True)
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
        sample_quality = benchmark_sample_quality(benchmark_events)

        with st.expander("Är benchmarken representativ?", expanded=True):
            q1, q2, q3 = st.columns(3)
            q1.metric("Referensevent", sample_quality["reference_events"])
            q2.metric(
                "Discovery-segment",
                f'{sample_quality["represented_segment_count"]}/{sample_quality["expected_segment_count"]}',
            )
            dominant = sample_quality.get("dominant_category")
            q3.metric(
                "Största kategori",
                f'{dominant["share_percent"]:.0f} %' if dominant else "–",
                help=dominant["name"] if dominant else None,
            )

            if sample_quality["warnings"]:
                for warning in sample_quality["warnings"]:
                    st.warning(warning)

            segment_rows = [{
                "Discovery-segment": segment,
                "Referensevent": sample_quality["segment_counts"].get(segment, 0),
                "Status": "Representerat" if sample_quality["segment_counts"].get(segment, 0) else "Blind fläck",
            } for segment in sample_quality["expected_segments"]]
            st.dataframe(pd.DataFrame(segment_rows), hide_index=True, use_container_width=True)
            st.caption(
                "Detta mäter kvaliteten på själva referensmängden – inte Upplevios täckning. "
                "Segmenten är grova kontrollgrupper för att upptäcka ensidighet, inte en ny produkttaxonomi."
            )

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
        checked_dates = sorted({x.checked_at for x in benchmark_events if x.checked_at})
        reference_sources = sorted({x.reference_source for x in benchmark_events if x.reference_source})
        checked_label = checked_dates[-1] if checked_dates else "okänt datum"
        st.caption(
            f"Avser endast den manuellt kontrollerade referensmängden för Örebro 4 sep–3 okt 2026. "
            f"Senast verifierad {checked_label}; {len(reference_sources)} referenskällor. "
            "Det är inte marknadstäckning för alla event i Örebro."
        )
        if bench["missed_events"]:
            st.markdown("#### Var finns luckorna?")
            if bench.get("segment_gaps"):
                segment_gap_rows = [{
                    "Discovery-segment": x["segment"],
                    "Referensevent": x["reference_events"],
                    "Missade": x["missed"],
                    "Täckning": f'{x["coverage_percent"]:.1f}%' if x["coverage_percent"] is not None else "–",
                } for x in bench["segment_gaps"]]
                st.caption("Prioritera breda discovery-luckor före enskilda venues eller nya funktioner")
                st.dataframe(pd.DataFrame(segment_gap_rows), use_container_width=True, hide_index=True)
            gap_cols = st.columns(2)
            with gap_cols[0]:
                category_rows = [{
                    "Kategori": x["category"],
                    "Referensevent": x["reference_events"],
                    "Missade": x["missed"],
                    "Täckning": f'{x["coverage_percent"]:.1f}%' if x["coverage_percent"] is not None else "–",
                } for x in bench["category_gaps"]]
                st.caption("Kategorier med minst ett missat referensevent")
                st.dataframe(pd.DataFrame(category_rows), use_container_width=True, hide_index=True)
            with gap_cols[1]:
                source_gap_rows = [{
                    "Referenskälla": x["reference_source"],
                    "Missade": x["missed"],
                    "Referensevent": x["reference_events"],
                    "Täckning": f'{x["coverage_percent"]:.1f}%' if x["coverage_percent"] is not None else "–",
                } for x in bench["source_gap_priority"]]
                st.caption("Referenskällor sorterade efter antal missade event")
                st.dataframe(pd.DataFrame(source_gap_rows), use_container_width=True, hide_index=True)

            if bench["venue_gaps"]:
                with st.expander("Platser med återkommande benchmark-luckor", expanded=False):
                    venue_rows = [{
                        "Plats": x["venue"],
                        "Referensevent": x["reference_events"],
                        "Missade": x["missed"],
                        "Täckning": f'{x["coverage_percent"]:.1f}%' if x["coverage_percent"] is not None else "–",
                    } for x in bench["venue_gaps"]]
                    st.dataframe(pd.DataFrame(venue_rows), use_container_width=True, hide_index=True)

            st.caption(
                "Luckdiagnostiken gäller bara den här benchmark-samplingen. Den används för att prioritera nästa källspår, "
                "inte för att påstå vilka kategorier eller platser som generellt saknas i hela Örebro."
            )
            with st.expander(f"Missade benchmark-event ({bench['missed']})", expanded=True):
                rows = [{
                    "Datum": x.start_date, "Event": x.title, "Kategori": x.category, "Plats": x.venue,
                    "Referens": x.reference_source, "Kontrollerad": x.checked_at
                } for x in bench["missed_events"]]
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else:
            st.success("Alla event i den aktuella benchmark-referensen hittades i importen.")
    except Exception as exc:
        st.warning(f"Benchmark kunde inte läsas: {exc}")
    st.markdown("### Kvalitet i standardresultaten · topp 10")
    default_quality_candidates = []
    for e in future_events:
        try:
            starts = date.fromisoformat(e.start_date)
        except Exception:
            continue
        if not (today <= starts <= today + timedelta(days=7)):
            continue
        dist = distance_from_city(e, DISCOVERY_DEFAULTS["city"])
        if dist is None or dist > DISCOVERY_DEFAULTS["radius_km"]:
            continue
        default_quality_candidates.append(e)
    default_ranked = rank_discovery(
        default_quality_candidates,
        origin_city=DISCOVERY_DEFAULTS["city"],
        price_filter=DISCOVERY_DEFAULTS["price"],
        query="",
        today=today,
        interests=[],
    )
    quality = discovery_quality_report([e for _, e in default_ranked], top_n=10)
    q1, q2, q3 = st.columns(3)
    q1.metric("Analyserade toppresultat", quality["events_analyzed"])
    q2.metric("Nästan-dubletter", len(quality["near_duplicate_pairs"]))
    q3.metric("Svaga titlar", len(quality["weak_title_events"]))
    st.caption(
        "Kontrollen använder Upplevios standardvy: Örebro · nästa 7 dagar · 50 km · alla priser. "
        "Detta är diagnostik, inte ett dolt filter; long-tail-event tas inte bort bara för att metadata är tunn."
    )
    if quality["warnings"]:
        for warning in quality["warnings"]:
            st.warning(warning)
    elif quality["events_analyzed"]:
        st.success("Inga tydliga kvalitetsvarningar i de analyserade toppresultaten.")
    else:
        st.info("För få standardresultat för att bedöma toppresultatens kvalitet just nu.")

    concentration_rows = []
    if quality.get("source_concentration"):
        x = quality["source_concentration"]
        concentration_rows.append({"Dimension": "Källa", "Dominerar": x["name"], "Andel": f'{x["share_percent"]:.0f} %'})
    if quality.get("type_concentration"):
        x = quality["type_concentration"]
        concentration_rows.append({"Dimension": "Typ", "Dominerar": x["name"], "Andel": f'{x["share_percent"]:.0f} %'})
    if concentration_rows:
        st.dataframe(pd.DataFrame(concentration_rows), use_container_width=True, hide_index=True)

    if quality["near_duplicate_pairs"]:
        with st.expander("Nästan-dubletter i topp 10", expanded=False):
            st.dataframe(pd.DataFrame([{
                "A": x["title_a"], "B": x["title_b"], "Datum": x["date"], "Titellikhet": f'{x["similarity"]:.0%}'
            } for x in quality["near_duplicate_pairs"]]), use_container_width=True, hide_index=True)
    if quality["weak_title_events"] or quality["metadata_issue_events"]:
        with st.expander("Titlar och metadata att granska", expanded=False):
            issues = {}
            for row in quality["weak_title_events"]:
                issues.setdefault(row["title"], []).append(row["issue"])
            for row in quality["metadata_issue_events"]:
                issues.setdefault(row["title"], []).extend(row["issues"])
            st.dataframe(pd.DataFrame([
                {"Event": title, "Kontroll": " · ".join(dict.fromkeys(problem_list))}
                for title, problem_list in issues.items()
            ]), use_container_width=True, hide_index=True)

    st.markdown("### Discovery Data Quality Gate")
    gate_report = discovery_data_quality_report([e for e in events if not e.is_demo])
    g1, g2, g3 = st.columns(3)
    g1.metric("Godkänd kärndata", gate_report["pass"])
    g2.metric("Begränsad ranking", gate_report["restricted"])
    g3.metric("Granska konsistens", gate_report["review"])
    st.caption(
        "Grinden påverkar bara central integritet: titel, giltiga datum och minst venue eller ort. "
        "Saknad start-/sluttid, pris, åldersgräns, dörrtid eller bokningslänk ger inget rankingstraff. "
        "Begränsade event kan fortfarande visas men deras organiska score får inte dominera toppen."
    )
    if gate_report["rows"]:
        with st.expander("Visa event som begränsas eller bör granskas", expanded=False):
            st.dataframe(pd.DataFrame([{
                "Event": row["title"],
                "Datum": row["date"],
                "Källa": ", ".join(row["sources"]),
                "Nivå": "Begränsad ranking" if row["level"] == "restricted" else "Granska",
                "Orsak": " · ".join(row["reasons"]),
            } for row in gate_report["rows"]]), use_container_width=True, hide_index=True)

    st.markdown("### Resultattillit & parserbrus")
    trust_report = result_trust_report([e for e in events if not e.is_demo])
    t1, t2, t3 = st.columns(3)
    t1.metric("Importerade event", trust_report["events_analyzed"])
    t2.metric("Dolt högkonfidens-brus", trust_report["suppressed_high_confidence"])
    t3.metric("Behöver granskas", trust_report["review_events"])
    st.caption(
        "Endast tydlig navigations-/knapptext, URL-liknande titlar eller rena datum/tider döljs automatiskt. "
        "Tunn metadata, saknad starttid och generiska men möjliga eventtitlar ligger kvar i discovery."
    )
    if trust_report["source_rows"]:
        st.dataframe(pd.DataFrame([{
            "Källa": row["source"],
            "Tydligt brus": row["high_confidence_noise"],
            "Granska": row["review"],
        } for row in trust_report["source_rows"]]), use_container_width=True, hide_index=True)
    if trust_report["high_confidence_events"] or trust_report["review_rows"]:
        with st.expander("Visa brus- och granskningsposter", expanded=False):
            trust_rows = []
            for row in trust_report["high_confidence_events"] + trust_report["review_rows"]:
                trust_rows.append({
                    "Event": row["title"], "Datum": row["date"],
                    "Källa": ", ".join(row["sources"]),
                    "Åtgärd": "Dold" if row["severity"] == "high" else "Granska",
                    "Orsak": " · ".join(row["reasons"]),
                })
            st.dataframe(pd.DataFrame(trust_rows), use_container_width=True, hide_index=True)

    st.markdown("### Källornas unika värde · 30 dagar")
    value_report = source_value_report(events, horizon_days=30, today=today)
    v1, v2, v3 = st.columns(3)
    v1.metric("Event i analysen", value_report["events"])
    v2.metric("Endast en källa", value_report["sole_source_events"])
    v3.metric("Flera källor", value_report["multi_source_events"])
    if value_report["sources"]:
        value_rows = [{
            "Källa": row["source"],
            "Event": row["represented_events"],
            "Unika": row["unique_events"],
            "Överlapp": row["overlap_events"],
            "Unik andel": f'{row["unique_share_percent"]:.0f} %' if row["unique_share_percent"] is not None else "–",
            "Signal": row["signal"],
        } for row in value_report["sources"]]
        st.dataframe(pd.DataFrame(value_rows), use_container_width=True, hide_index=True)
        st.caption(
            "Unik betyder att eventet, efter Upplevios konservativa deduplicering, bara finns från den källan i aktuell 30-dagarsvy. "
            "Det är en ögonblicksbild – ta inte bort en källa enbart på denna tabell."
        )
        if value_report["overlap_pairs"]:
            with st.expander("Vilka källor överlappar varandra?", expanded=False):
                overlap_rows = [{
                    "Källa A": row["source_a"],
                    "Källa B": row["source_b"],
                    "Gemensamma event": row["shared_events"],
                } for row in value_report["overlap_pairs"]]
                st.dataframe(pd.DataFrame(overlap_rows), use_container_width=True, hide_index=True)
                st.caption("Visar bara event som Upplevio faktiskt har slagit ihop som samma event. Tveksamma dublettkandidater räknas inte som överlapp.")
    else:
        st.info("Det finns inga kommande event med källinformation i den aktuella 30-dagarsperioden.")

    st.markdown("### Booking funnel intelligence")
    _funnel = funnel_report(events)
    _ft = _funnel["totals"]
    f1,f2,f3 = st.columns(3)
    f1.metric("Visningar", _ft["impressions"])
    f2.metric("Öppnade detaljer", _ft["opens"])
    f3.metric("Bokningsklick", _ft["booking_clicks"])
    if _ft["impressions"]:
        st.caption(
            f"Öppningsgrad: {(_ft['open_rate'] or 0)*100:.1f}% · "
            f"Bokningsklick/visning: {(_ft['booking_click_rate'] or 0)*100:.1f}%"
        )
    else:
        st.caption("Ingen funnel-data ännu. Mätningen börjar först när denna release används.")
    if _funnel["by_source"]:
        with st.expander("Funnel per källa", expanded=True):
            st.dataframe(pd.DataFrame([{
                "Källa":r["source"],
                "Visningar":r["impressions"],
                "Öppningar":r["opens"],
                "Bokningsklick":r["booking_clicks"],
                "Öppningsgrad":f"{(r['open_rate'] or 0)*100:.1f}%" if r["open_rate"] is not None else "—",
                "Klick/visning":f"{(r['booking_click_rate'] or 0)*100:.1f}%" if r["booking_click_rate"] is not None else "—",
            } for r in _funnel["by_source"]]), use_container_width=True, hide_index=True)
        with st.expander("Funnel per eventtyp", expanded=False):
            st.dataframe(pd.DataFrame([{
                "Eventtyp":r["event_type"],
                "Visningar":r["impressions"],
                "Öppningar":r["opens"],
                "Bokningsklick":r["booking_clicks"],
                "Klick/visning":f"{(r['booking_click_rate'] or 0)*100:.1f}%" if r["booking_click_rate"] is not None else "—",
            } for r in _funnel["by_event_type"]]), use_container_width=True, hide_index=True)
        with st.expander("Funnel per bokningspartner", expanded=False):
            st.dataframe(pd.DataFrame([{
                "Partner":r["partner"],
                "Visningar":r["impressions"],
                "Öppningar":r["opens"],
                "Bokningsklick":r["booking_clicks"],
                "Klick/visning":f"{(r['booking_click_rate'] or 0)*100:.1f}%" if r["booking_click_rate"] is not None else "—",
            } for r in _funnel["by_partner"]]), use_container_width=True, hide_index=True)
    st.caption(
        "Funnel-måtten skiljer på visning, faktisk detaljöppning och bokningsutklick. Ett bokningsklick är inte samma sak som en genomförd bokning."
    )

    st.markdown("### Kandidataudit · lokala källor + Örebro universitet")
    st.caption("Kandidaterna hämtas bara i Admin och läggs aldrig i publik discovery. Örebro universitet filtreras konservativt till lokala poster som uttryckligen är märkta Öppet för alla.")
    if st.button("Kör kandidataudit", key="run-candidate-audit", use_container_width=True):
        with st.spinner("Jämför kandidatkalendrar mot aktuell Upplevio-import…"):
            _candidate_rows, _candidate_health = fetch_candidate_sources()
            _candidate_audit = candidate_value_audit(events, _candidate_rows)
            record_candidate_snapshot(_candidate_audit, _candidate_health)
            st.session_state["candidate_audit_rows"] = _candidate_audit
            st.session_state["candidate_audit_health"] = _candidate_health
    _candidate_audit = st.session_state.get("candidate_audit_rows", [])
    _candidate_health = st.session_state.get("candidate_audit_health", [])
    if _candidate_health:
        st.dataframe(pd.DataFrame([{
            "Kandidatkälla": r["source"], "Status": r["status"], "Hittade event": r["events"],
            "Fel": r["error"] or ""
        } for r in _candidate_health]), use_container_width=True, hide_index=True)
    if _candidate_audit:
        st.dataframe(pd.DataFrame([{
            "Kandidatkälla": r["source"],
            "Parserträffar": r["candidate_events"],
            "Efter dedupe": r["represented_after_dedupe"],
            "Unika event": r["unique_events"],
            "Överlapp": r["overlap_events"],
            "Unik andel": f"{(r['unique_share'] or 0)*100:.0f}%" if r["unique_share"] is not None else "—",
            "Bokningsbara": r["bookable"],
            "Eventtyper": ", ".join(r["event_types"]) or "—",
            "Eventtyper bland egna unika event": ", ".join(r["unique_event_types"]) or "—",
            "Frontier-segment": ", ".join(r.get("frontier_segments") or []) or "—",
            "Unika frontier-segment": ", ".join(r.get("unique_frontier_segments") or []) or "—",
            "Fyller tunn/saknad täckning": ", ".join(r.get("underserved_segments") or []) or "—",
            "Unika event i tunn/saknad täckning": r.get("unique_events_in_underserved_segments", 0),
        } for r in _candidate_audit]), use_container_width=True, hide_index=True)
        st.caption("'Unik' betyder att kandidat-eventet efter Upplevios vanliga dedupe inte slogs ihop med någon befintlig källa. Frontier-värdet visar dessutom om de unika eventen fyller segment som i aktuell import är tunna eller saknas. Resultatet sparas som dagens kandidat-snapshot.")

    _candidate_decisions = candidate_decisions()
    if _candidate_decisions:
        st.markdown("#### Kandidatbeslut över tid")
        st.dataframe(pd.DataFrame([{
            "Källa": d.source,
            "Beslut": d.decision,
            "Snapshots": d.snapshots,
            "Dagar": d.distinct_days,
            "Parserstabilitet": f"{(d.parser_success_rate or 0)*100:.0f}%" if d.parser_success_rate is not None else "—",
            "Median unika event": f"{d.median_unique_events:.0f}" if d.median_unique_events is not None else "—",
            "Median unik andel": f"{d.median_unique_share*100:.0f}%" if d.median_unique_share is not None else "—",
            "Unika eventtyper": ", ".join(d.observed_unique_event_types) or "—",
            "Unika frontier-segment": ", ".join(d.observed_unique_frontier_segments) or "—",
            "Tunn/saknad täckning som fyllts": ", ".join(d.observed_underserved_segments) or "—",
            "Median unika gap-event": f"{d.median_unique_events_in_underserved_segments:.0f}" if d.median_unique_events_in_underserved_segments is not None else "—",
        } for d in _candidate_decisions]), use_container_width=True, hide_index=True)
        for d in _candidate_decisions:
            with st.expander(f"{d.source} · {d.decision}", expanded=False):
                for reason in d.reasons:
                    st.write("• " + reason)
        st.caption(
            "Aktivera kräver minst tre snapshots på tre olika dagar, stabil parser och återkommande unik nytta. "
            "Avstå kräver flera mätningar med tydligt låg nytta eller parserproblem. Kandidatmotorn väger nu även in återkommande unika event i Coverage Frontier-segment som är tunna eller saknas. Bokningsgrad visas i auditen men är inte ett krav för fria/offentliga aktiviteter."
        )

        _candidate_portfolio = candidate_portfolio()
        if _candidate_portfolio:
            st.markdown("#### Kandidatportfölj · arbetsprioritet")
            st.dataframe(pd.DataFrame([{
                "Källa": r.source,
                "Arbetsprioritet": r.priority,
                "Evidens": r.evidence,
                "Aktiveringsbeslut": r.activation_decision,
                "Dagar": r.distinct_days,
                "Parserstabilitet": f"{(r.parser_success_rate or 0)*100:.0f}%" if r.parser_success_rate is not None else "—",
                "Median unika event": f"{r.median_unique_events:.0f}" if r.median_unique_events is not None else "—",
                "Median unik andel": f"{r.median_unique_share*100:.0f}%" if r.median_unique_share is not None else "—",
                "Median gap-event": f"{r.median_gap_events:.0f}" if r.median_gap_events is not None else "—",
            } for r in _candidate_portfolio]), use_container_width=True, hide_index=True)
            for r in _candidate_portfolio:
                with st.expander(f"{r.source} · {r.priority}", expanded=False):
                    for reason in r.reasons:
                        st.write("• " + reason)
            st.caption(
                "Portföljvyn är en arbetsprioritering, inte en ny aktiveringsmotor och inte en poängmodell. "
                "Kandidatbeslutet ovan är fortfarande auktoriteten för Aktivera/Fortsätt mäta/Avstå. "
                "Syftet är att synliggöra parserproblem och källor som återkommande ger liten unik nytta så att underhåll kan prioriteras."
            )

    st.markdown("### Örebro Coverage Frontier · 30/60/90 dagar")
    _frontier = coverage_frontier(events, today=today)
    _frontier_rows = _frontier["rows"]
    st.dataframe(pd.DataFrame([{
        "Segment": r["segment"],
        "Status": r["status"],
        "30 d": r["events_30"],
        "60 d": r["events_60"],
        "90 d": r["events_90"],
        "Källor": r["source_diversity"],
        "Betrodda källor": r["trusted_source_count"],
        "Enkällsberoende": "Ja" if r["single_source_dependency"] else "Nej",
    } for r in _frontier_rows]), use_container_width=True, hide_index=True)
    with st.expander("Visa källor per frontier-segment", expanded=False):
        for r in _frontier_rows:
            st.write(f"**{r['segment']} · {r['status']}**")
            st.caption(", ".join(r["sources"]) or "Ingen källa representerad i aktuell import")
    st.caption(
        "Frontiern beskriver endast aktuell import — inte hela Örebros eventmarknad. "
        "'Saknas' betyder därför 'saknas i aktuell import'. Ingen viktad totalscore används."
    )

    st.markdown("### Lokala källors faktiska värde · 30 dagar")
    _local_audit = local_source_audit(events, horizon_days=30, today=today)
    if _local_audit["sources"]:
        st.dataframe(pd.DataFrame([{
            "Källa": r["source"],
            "Event": r["represented_events"],
            "Unika event": r["unique_events"],
            "Unik andel": f"{(r['unique_share'] or 0)*100:.0f}%",
            "Eventtyper": r["category_count"],
            "Eventtyper bland egna unika event": r["unique_category_count"],
            "Bokningsbara": r["bookable_events"],
            "Bokningstäckning": f"{(r['booking_coverage'] or 0)*100:.0f}%",
        } for r in _local_audit["sources"]]), use_container_width=True, hide_index=True)
        with st.expander("Visa källornas kategoribidrag", expanded=False):
            for r in _local_audit["sources"]:
                st.write(f"**{r['source']}** · {', '.join(r['categories']) or '—'}")
                if r["unique_categories"]:
                    st.caption("Unikt i aktuell import: " + ", ".join(r["unique_categories"]))
    else:
        st.info("Ingen lokal källdata i den aktuella 30-dagarsperioden.")
    st.caption(
        "Det här är en snapshot av aktuell importerad data. 'Unik' betyder att eventet efter dedupe bara representeras av en källa. "
        "Ingen totalscore används; volym, unikhet, kategoribidrag och bokningsgrad visas separat."
    )

    st.markdown("### Detaljtäckning & trust · 30 dagar")
    _detail_audit = detail_coverage_audit(events, horizon_days=30, today=today)
    _detail_summary = _detail_audit["summary"]
    _dc1, _dc2, _dc3, _dc4 = st.columns(4)
    _dc1.metric("Starttid", f"{(_detail_summary['start_time_coverage'] or 0)*100:.0f}%")
    _dc2.metric("Exakt tidsintervall", f"{(_detail_summary['time_range_coverage'] or 0)*100:.0f}%")
    _dc3.metric("Preciserad plats", f"{(_detail_summary['precise_venue_coverage'] or 0)*100:.0f}%")
    _dc4.metric("Prisstatus känd", f"{(_detail_summary['price_coverage'] or 0)*100:.0f}%")
    if _detail_audit["sources"]:
        st.dataframe(pd.DataFrame([{
            "Källa": r["source"],
            "Event": r["represented_events"],
            "Enkällsevent": r["single_source_events"],
            "Starttid": f"{(r['start_time_coverage'] or 0)*100:.0f}%",
            "Sluttid": f"{(r['end_time_coverage'] or 0)*100:.0f}%",
            "Preciserad plats": f"{(r['precise_venue_coverage'] or 0)*100:.0f}%",
            "Pris": f"{(r['price_coverage'] or 0)*100:.0f}%",
            "Åldersgräns": f"{(r['age_limit_coverage'] or 0)*100:.0f}%",
            "Dörr/insläpp": f"{(r['door_time_coverage'] or 0)*100:.0f}%",
            "Bokningslänk": f"{(r['booking_coverage'] or 0)*100:.0f}%",
            "Signal": " · ".join(r["flags"]),
        } for r in _detail_audit["sources"]]), use_container_width=True, hide_index=True)
        with st.expander("Så ska detaljauditen tolkas", expanded=False):
            st.write("• Tabellen mäter den färdiga, deduplicerade eventkvaliteten som varje källa representerar.")
            st.write("• Om ett event har flera källor kan ett detaljfält ha kommit från någon av dem; därför visas Enkällsevent som renare attribueringssignal.")
            st.write("• Preciserad plats betyder en namngiven plats/lokal, inte bara exempelvis Örebro eller generiska Conventum.")
            st.write("• Pris räknas bara när prisstatus är uttryckligen känd eller gratis. Okänt pris räknas aldrig som gratis.")
            st.write("• Signalerna är transparenta trösklar, inte en dold kvalitetspoäng.")
    else:
        st.info("Ingen detaljdata i den aktuella 30-dagarsperioden.")
    st.caption(
        "Detaljtäckningen visar vad den aktuella importen faktiskt vet om sina event. Den är inte marknadstäckning och "
        "påstår inte fältproveniens när flera källor har slagits ihop. Målet är att hitta nästa konkreta datakvalitetslucka."
    )

    st.markdown("#### Nästa detaljluckor att förbättra")
    _gap_priorities = detail_gap_priorities(_detail_audit)
    if _gap_priorities:
        st.dataframe(pd.DataFrame([{
            "Prioritet": r["priority"],
            "Källa": r["source"],
            "Fält": r["field_label"],
            "Täckning": f"{r['coverage']*100:.0f}%",
            "Saknas": r["missing_events"],
            "Saknas · enkällsevent": r["single_source_missing_events"],
            "Varför": r["reason"],
        } for r in _gap_priorities[:12]]), use_container_width=True, hide_index=True)
    else:
        st.success("Inga tydliga detaljluckor behöver prioriteras i den aktuella 30-dagarsmätningen.")
    st.caption(
        "Prioriteringen använder ingen totalscore. Högst går återkommande luckor i enkällsevent, därefter större luckor med fler-källproveniens. "
        "Små stickprov markeras som För lite data i stället för att driva parserarbete."
    )

    if _gap_priorities:
        st.markdown("#### Gap → fix · konkreta parserfall")
        _workflow_options = _gap_priorities[:12]
        _workflow_labels = [
            f"{r['priority']} · {r['source']} → {r['field_label']} · {r['single_source_missing_events']} rena / {r['missing_events']} totalt"
            for r in _workflow_options
        ]
        _selected_workflow_label = st.selectbox(
            "Välj detaljlucka att felsöka", _workflow_labels, key="detail_gap_workflow_select"
        )
        _selected_gap = _workflow_options[_workflow_labels.index(_selected_workflow_label)]
        _workflow_cases = detail_gap_cases(
            events, source=_selected_gap["source"], field=_selected_gap["field"],
            horizon_days=_detail_audit["horizon_days"], today=today, limit=50,
        )
        _workflow_summary = gap_workflow_summary(_workflow_cases)
        _gw1, _gw2, _gw3 = st.columns(3)
        _gw1.metric("Event att granska", _workflow_summary["cases"])
        _gw2.metric("Rena enkällsfall", _workflow_summary["clean_cases"])
        _gw3.metric(
            "Med gransknings-URL",
            f"{(_workflow_summary['url_coverage'] or 0)*100:.0f}%" if _workflow_summary["cases"] else "—",
        )
        st.caption(_selected_gap["reason"] + " Enkällsevent visas först eftersom parseransvaret där är tydligast.")
        if _workflow_cases:
            _workflow_df = pd.DataFrame([{
                "Attribution": r["attribution"],
                "Datum": r["date"],
                "Tid": r["start_time"] or "—",
                "Event": r["title"],
                "Plats": r["venue"] or "—",
                "Granska sida": r["url"],
                "URL-underlag": r["url_basis"],
                "Källor": r["sources"],
            } for r in _workflow_cases])
            st.dataframe(
                _workflow_df, use_container_width=True, hide_index=True,
                column_config={
                    "Granska sida": st.column_config.LinkColumn("Granska sida", display_text="Öppna"),
                },
            )
        else:
            st.info("Inga konkreta eventfall hittades för den valda luckan i aktuell 30-dagarsimport.")
        st.caption(
            "Workflowet gör inga nya nätverksanrop. För fler-källevent används i första hand den valda källans egen source_url; "
            "därmed minskar risken att en parser felsöks mot en annan källas sida efter dedupe."
        )

        if _workflow_cases:
            st.markdown("##### Parser-evidens · granska ett konkret fall")
            _evidence_cases = [r for r in _workflow_cases if r.get("url")][:12]
            if _evidence_cases:
                _evidence_labels = [f"{r['date']} · {r['title']} · {r['attribution']}" for r in _evidence_cases]
                _selected_evidence_label = st.selectbox("Välj eventsida", _evidence_labels, key="parser_evidence_case_select")
                _evidence_case = _evidence_cases[_evidence_labels.index(_selected_evidence_label)]
                if st.button("Granska sidan efter evidens", key="parser_evidence_fetch"):
                    with st.spinner("Granskar den valda eventsidan …"):
                        _evidence = fetch_gap_evidence(
                            _evidence_case["url"], field=_selected_gap["field"],
                            current_start_time=_evidence_case.get("start_time") or None, timeout=10,
                        )
                    st.session_state["parser_evidence_result"] = {
                        "case": _evidence_case["event_id"], "field": _selected_gap["field"], "result": _evidence
                    }
                _stored = st.session_state.get("parser_evidence_result")
                if _stored and _stored.get("case") == _evidence_case["event_id"] and _stored.get("field") == _selected_gap["field"]:
                    _ev = _stored["result"]
                    if _ev["status"] == "Parserkandidat":
                        st.warning(f"**{_ev['status']}** · sidan verkar innehålla data som parsern kan missa.")
                    elif _ev["status"] in {"Källan verkar sakna uppgiften", "Källan saknar exakt värde"}:
                        st.info(f"**{_ev['status']}**")
                    else:
                        st.write(f"**{_ev['status']}**")
                    if _ev.get("value") is not None:
                        st.write(f"Identifierat värde: `{_ev['value']}`")
                    st.caption(_ev["explanation"])
                    if _ev.get("snippet"):
                        st.code(_ev["snippet"], language=None)
                    st.caption("Evidensvyn är diagnostik: den ändrar aldrig eventet eller parsern automatiskt.")
            else:
                st.info("Inget av de konkreta fallen har en granskningsbar URL.")

            if _evidence_cases:
                st.markdown("##### Batch-evidens · finns ett återkommande parserfel?")
                st.caption("Granskar upp till 9 URL-fall, med rena enkällsfall först. Resultatet är diagnostik och ändrar aldrig parser eller eventdata.")
                if st.button("Granska flera fall", key="parser_evidence_batch_fetch"):
                    with st.spinner("Granskar flera eventsidor …"):
                        _batch = evidence_batch_audit(
                            _evidence_cases, field=_selected_gap["field"], limit=9, timeout=8, max_workers=4
                        )
                    st.session_state["parser_evidence_batch_result"] = {
                        "source": _selected_gap["source"], "field": _selected_gap["field"], "result": _batch
                    }
                _batch_stored = st.session_state.get("parser_evidence_batch_result")
                if (_batch_stored and _batch_stored.get("source") == _selected_gap["source"]
                        and _batch_stored.get("field") == _selected_gap["field"]):
                    _ba = _batch_stored["result"]
                    _b1, _b2, _b3 = st.columns(3)
                    _b1.metric("Analyserbara sidor", _ba["analyzable"])
                    _b2.metric("Parserkandidater", _ba["parser_candidates"])
                    _b3.metric("Andel", f"{(_ba['candidate_rate'] or 0)*100:.0f}%" if _ba["candidate_rate"] is not None else "—")
                    if _ba["classification"] == "Återkommande parserkandidat":
                        st.warning(f"**{_ba['classification']}** · samma typ av miss verkar återkomma på flera sidor.")
                    elif _ba["classification"] == "Ingen parsertrend hittad":
                        st.info(f"**{_ba['classification']}** · de granskade sidorna verkar oftare sakna uppgiften än parsern missa den.")
                    else:
                        st.write(f"**{_ba['classification']}**")
                    if _ba["rows"]:
                        st.dataframe(pd.DataFrame([{
                            "Datum": r["date"], "Event": r["title"], "Attribution": r["attribution"],
                            "Status": r["status"], "Värde": r["value"] if r["value"] is not None else "—",
                            "HTTP": r["http_status"] if r["http_status"] is not None else "—",
                            "Sida": r["url"],
                        } for r in _ba["rows"]]), use_container_width=True, hide_index=True,
                        column_config={"Sida": st.column_config.LinkColumn("Sida", display_text="Öppna")})
                    st.caption("Hämtningsfel räknas inte in i andelen parserkandidater. Minst tre analyserbara sidor krävs innan en återkommande parsertrend markeras.")

                    st.markdown("##### Rekommenderad parserfix")
                    _rec = build_parser_fix_recommendation(_ba, source=_selected_gap["source"])
                    if _rec.get("ready"):
                        st.warning(f"**Förslag:** `{_rec['target_module']}::{_rec['target_function']}`")
                        st.write(_rec["recommendation"])
                        st.caption(_rec["evidence_summary"])
                        if _rec.get("examples"):
                            st.write("**Evidensexempel**")
                            for _ex in _rec["examples"]:
                                _value = f" → `{_ex['value']}`" if _ex.get("value") is not None else ""
                                st.markdown(f"- **{_ex['date']} · {_ex['title']}**{_value}")
                                if _ex.get("snippet"):
                                    st.code(_ex["snippet"], language=None)
                        st.write("**Regressionstester som krävs före fix**")
                        for _test in _rec["required_tests"]:
                            st.markdown(f"- {_test}")
                        st.caption(_rec["guardrail"])
                    else:
                        st.info(f"Ingen parserfix rekommenderas ännu: {_rec.get('reason', 'otillräcklig evidens')}")

                    st.markdown("##### Parserfix-impact · replay mot pre-v0.74")
                    if _selected_gap["field"] in {"start_time", "price"}:
                        st.caption("Jämför samma eventsidor med parserbeteendet före v0.74 och den aktuella parsern. Detta mäter kodfixens effekt på underlaget, inte ännu live-produktionspåverkan.")
                        if st.button("Mät parserfixens replay-effekt", key="parser_fix_impact_fetch"):
                            with st.spinner("Spelar om eventsidor genom gammal och ny parser …"):
                                _impact = parser_fix_impact_audit(
                                    _evidence_cases, field=_selected_gap["field"], limit=9, timeout=8, max_workers=4
                                )
                            st.session_state["parser_fix_impact_result"] = {
                                "source": _selected_gap["source"], "field": _selected_gap["field"], "result": _impact
                            }
                        _impact_stored = st.session_state.get("parser_fix_impact_result")
                        if (_impact_stored and _impact_stored.get("source") == _selected_gap["source"]
                                and _impact_stored.get("field") == _selected_gap["field"]):
                            _ia = _impact_stored["result"]
                            _i1, _i2, _i3 = st.columns(3)
                            _i1.metric("Analyserbara", _ia["analyzable"])
                            _i2.metric("Återvunna värden", _ia["recovered"])
                            _i3.metric("Regressioner/ändrade", _ia["regressions"] + _ia["changed"])
                            if _ia["classification"] == "Mätbar förbättring i replay":
                                st.success(f"**{_ia['classification']}**")
                            elif _ia["classification"] == "Granska avvikelse":
                                st.error(f"**{_ia['classification']}** · minst ett fall beter sig sämre eller annorlunda än tidigare.")
                            else:
                                st.info(f"**{_ia['classification']}**")
                            st.dataframe(pd.DataFrame([{
                                "Datum": r.get("date", ""), "Event": r.get("title", ""),
                                "Före v0.74": r.get("legacy") if r.get("legacy") is not None else "—",
                                "Nu": r.get("current") if r.get("current") is not None else "—",
                                "Utfall": r.get("outcome", ""), "Sida": r.get("url", ""),
                            } for r in _ia["rows"]]), use_container_width=True, hide_index=True,
                            column_config={"Sida": st.column_config.LinkColumn("Sida", display_text="Öppna")})
                            st.caption(_ia["note"])
                    else:
                        st.caption("v0.74 ändrade starttids- och prisparsern. För den valda luckan finns därför ingen relevant före/efter-replay att mäta i denna release.")

                    st.markdown("##### Parser Regression Guardrails")
                    _gr = run_guardrail_registry()
                    _g1, _g2, _g3 = st.columns(3)
                    _g1.metric("Guardrails", _gr["total"])
                    _g2.metric("Godkända", _gr["passed"])
                    _g3.metric("Fel", _gr["failed"])
                    if _gr["all_passed"]:
                        st.success("Alla registrerade parser-guardrails passerar i aktuell kod.")
                    else:
                        st.error("Minst en historisk parser-guardrail har brutits. Parserfix bör inte släppas innan avvikelsen är förstådd.")
                    st.dataframe(pd.DataFrame([{
                        "Källa": r["source"], "Fält": r["field"], "Typ": r["kind"],
                        "Fall": r["id"], "Förväntat": "—" if r["expected"] is None else str(r["expected"]),
                        "Nu": "—" if r["actual"] is None else str(r["actual"]),
                        "Status": "OK" if r["passed"] else "FEL", "Skydd": r["note"],
                    } for r in _gr["rows"]]), use_container_width=True, hide_index=True)
                    st.caption("Registret är nätverksfritt och kör minimala verklighetsnära HTML-fixtures. Det skyddar historiskt parserbeteende utan att vara beroende av att källwebbplatser är tillgängliga just nu.")

    st.markdown("### Bokningspartner & attribution")
    _partner_report = partner_report(events)
    _partner_rows = _partner_report["partners"]
    if _partner_rows:
        st.dataframe(pd.DataFrame([{
            "Partner": r["name"],
            "Bokningsbara event": r["bookable_events"],
            "Typ": "Direkt hos arrangör/annan domän" if r["direct"] else "Identifierad bokningsplattform",
            "Affiliate-status": {
                "enabled":"Aktiverad",
                "potential":"Potentiell",
                "unavailable":"Ej tillgänglig",
                "unassessed":"Ej bedömd",
            }.get(r["affiliate_status"], r["affiliate_status"])
        } for r in _partner_rows]), use_container_width=True, hide_index=True)
    else:
        st.info("Inga bokningspartner kan attribueras i aktuell import.")
    st.caption(
        "Partneridentifiering bygger på destinationsdomänen. Affiliate-status hålls separat och är 'Ej bedömd' tills ett faktiskt kommersiellt avtal eller verifierat program finns."
    )

    st.markdown("### Bokningstäckning per källa")
    _booking_cov = booking_coverage_report(events)
    _t = _booking_cov["totals"]
    c1,c2,c3 = st.columns(3)
    c1.metric("Event i mätningen", _t["total"])
    c2.metric("Med verifierad bokningsväg", _t["bookable"])
    c3.metric("Bokningstäckning", f"{_t['booking_coverage']*100:.0f}%")
    if _booking_cov["sources"]:
        st.dataframe(pd.DataFrame([{
            "Källa":r["source"], "Event":r["total"], "Bokningsbara":r["bookable"],
            "Täckning":f"{r['booking_coverage']*100:.0f}%", "Svaga länkar":r["weak"],
            "Saknar länk":r["missing"], "Bokningspartner":" · ".join(r["partners"].keys()) or "—"
        } for r in _booking_cov["sources"]]), use_container_width=True, hide_index=True)
    st.caption("KPI:n räknar bara verifierade boknings-/biljettvägar. Informationssidor räknas inte som bokning.")

    st.markdown("### Bokningsvägar")
    booking_quality_rows = []
    for _e in events:
        _q = cta_quality(_e)
        booking_quality_rows.append((_e, _q))
    _bookable = sum(1 for _, q in booking_quality_rows if q["status"] == "bookable")
    _useful = sum(1 for _, q in booking_quality_rows if q["status"] == "useful")
    _weak = sum(1 for _, q in booking_quality_rows if q["status"] == "weak")
    _missing = sum(1 for _, q in booking_quality_rows if q["status"] == "missing")
    b1,b2,b3,b4 = st.columns(4)
    b1.metric("Bokningsbara", _bookable)
    b2.metric("Användbara länkar", _useful)
    b3.metric("Svaga länkar", _weak)
    b4.metric("Saknar länk", _missing)
    st.caption("Boka/Köp biljett visas bara när länken ger tillräckligt stöd. En vanlig informationssida märks Läs mer.")
    if _weak:
        with st.expander("Svaga CTA-länkar", expanded=False):
            for _e, _q in booking_quality_rows:
                if _q["status"] == "weak":
                    st.write(f"**{_e.title}** · {_e.source} — {_q['reason']}")

    st.markdown("### Tracked booking redirect")
    _redirect_ready = bool(public_base_url and redirect_secret and len(redirect_secret) >= 32)
    r1,r2 = st.columns(2)
    r1.metric("Redirectspårning", "Redo" if _redirect_ready else "Ej aktiverad")
    r2.metric("Fail-safe direktlänk", "Ja")
    st.caption(
        "Spårning aktiveras bara när UPPLEVIO_PUBLIC_URL och en minst 32 tecken lång UPPLEVIO_REDIRECT_SECRET finns. "
        "Annars går användaren direkt till bokningspartnern som tidigare."
    )

    st.markdown("### Conversion attribution · grund")
    _attr = attribution_report()
    a1,a2,a3 = st.columns(3)
    a1.metric("Spårade bokningsklick", _attr["clicks"])
    a2.metric("Rapporterade konverteringar", _attr["conversions"])
    a3.metric("Bekräftade bokningar", _attr["confirmed"])
    st.caption(
        "Varje framtida bokningsutklick kan få ett eget Upplevio click-id. En partnercallback kan därefter kopplas tillbaka till exakt event, partner och eventuell sponsringskampanj. "
        "Ingen konvertering räknas utan återrapportering från partner."
    )
    if _attr["partners"]:
        st.dataframe(pd.DataFrame(_attr["partners"]), use_container_width=True, hide_index=True)

    st.markdown("### Intäktsberedskap · ej aktiverad")
    st.caption(
        "Teknisk grund för Hitta → Inspireras → Boka. Organisk ranking är fortsatt separat från kommersiell placering. "
        "Inga annonsytor eller sponsrade placeringar är aktiverade i användarvyn."
    )
    c1, c2, c3 = st.columns(3)
    c1.metric("Boknings-/affiliateflöde", "Förberett")
    c2.metric("Sponsringsmodell", "Förberedd")
    c3.metric("Annonsytor aktiva", sum(1 for slot in AD_SLOTS if slot.enabled))
    st.caption(
        "Mätmodellen stödjer impression → aktivitetsbesök → CTA-klick → externt bokningsklick samt kampanj-ID, företag och partner. "
        "Faktisk konverterad bokning kräver senare återrapportering från boknings-/affiliatepartner."
    )
    with st.expander("Framtida företagsvy – mätpunkter", expanded=False):
        st.write("Företagsvyn är ännu inte en publik portal. Den förberedda modellen kan visa visningar, aktivitetsbesök, sponsrade klick, bokningsklick och CTR per företag.")
        st.caption("Ingen påhittad demo-statistik visas. Värden ska komma från verklig mätdata.")

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
