import os
from datetime import date, datetime, timedelta, timezone
import streamlit as st
import pandas as pd

from sources import load_events
from dedupe import deduplicate
from db import favorite_ids, toggle_favorite, get_meta, set_meta, list_watches, add_watch, delete_watch
from source_registry import SOURCES
from coverage import CITY_COORDS, distance_from_city
from discovery import DEFAULT_INTERESTS, recommended_for_you, worth_a_trip, newly_announced, this_weekend, big_fairs
from taxonomy import collector_subcategories, collector_match

st.set_page_config(page_title="Upplevio", page_icon="✦", layout="wide")

st.markdown("""
<style>
:root{--ink:#111827;--muted:#6b7280;--line:#e5e7eb;--soft:#f5f5f2;--card:#fff}
.block-container{max-width:1240px;padding-top:1.0rem;padding-bottom:6rem}
[data-testid="stSidebar"]{background:#f7f7f5}
.hero{padding:18px 4px 8px}.eyebrow{font-size:.72rem;font-weight:800;letter-spacing:.14em;text-transform:uppercase;color:#6b7280}
.hero h1{font-size:clamp(2.35rem,5vw,4.7rem);letter-spacing:-.06em;line-height:.92;margin:.25rem 0 .8rem;color:#111827}
.hero p{max-width:720px;color:#6b7280;font-size:1.02rem}
.metric-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:12px 0 24px}
.metric-card,.event-card,.detail-box,.day-card{background:#fff;border:1px solid #e5e7eb;border-radius:20px}
.metric-card{padding:18px}.metric-n{font-size:2rem;font-weight:850;letter-spacing:-.04em}.metric-l{font-size:.84rem;color:#6b7280}
.section-title{font-size:1.35rem;font-weight:850;letter-spacing:-.03em;margin:26px 0 10px}
.event-card{padding:18px;margin-bottom:10px;min-height:205px;box-shadow:0 1px 0 rgba(17,24,39,.02)}
.badge{display:inline-block;background:#f1f1ef;border-radius:999px;padding:5px 9px;font-size:.72rem;font-weight:750;margin:0 4px 4px 0;color:#374151}
.badge-new{background:#111827;color:#fff}.badge-review{background:#fff1d6;color:#8a5a00}
.event-title{font-size:1.25rem;font-weight:850;letter-spacing:-.03em;margin:11px 0 5px}
.event-meta{color:#6b7280;font-size:.88rem;line-height:1.65}.source{font-size:.73rem;color:#9ca3af;margin-top:12px}
.detail-box{padding:24px}.day-card{padding:14px 16px;text-align:center}.day-n{font-size:1.45rem;font-weight:850}
div[data-testid="stButton"] button{border-radius:999px;min-height:42px}
@media(max-width:800px){
 .metric-grid{grid-template-columns:repeat(2,1fr);gap:8px}
 .metric-card{padding:14px}.metric-n{font-size:1.7rem}
 .block-container{padding-left:.85rem;padding-right:.85rem}
 .hero h1{font-size:2.7rem}
}
</style>
""", unsafe_allow_html=True)

def secret(name):
    try: return st.secrets.get(name)
    except Exception: return os.getenv(name)

api_key = secret("TICKETMASTER_API_KEY")
with st.sidebar:
    st.markdown("### Datakällor")
    experimental_sources = st.toggle("Testa officiella mässkalendrar", value=False, help="Experimentella parsers för officiella mässkalendrar. Avstängda som standard tills liveformatet verifierats.")
    experimental_collectors = st.toggle("Testa samlarkort/retro-källor", value=False, help="Experimentell import från specialiserade samlarkalendrar och biljettkällor.")
    experimental_entertainment = st.toggle("Testa stand-up/scenkällor", value=False, help="Experimentell kompletterande import från Showtic.")
experimental_keys = ["stockholmsmassan","elmia","malmomassan"] if experimental_sources else []
collector_keys = ["kortcentralen","tickster_collectors"] if experimental_collectors else []
entertainment_keys = ["showtic"] if experimental_entertainment else []
raw_events, source_health = load_events(
    api_key,
    include_visitsweden=True,
    experimental_official_keys=experimental_keys,
    experimental_collector_keys=collector_keys,
    experimental_entertainment_keys=entertainment_keys
)
events, review_pairs = deduplicate(raw_events)
today = date.today()

previous_visit_raw = get_meta("last_visit")
try:
    previous_visit = datetime.fromisoformat(previous_visit_raw) if previous_visit_raw else datetime.now(timezone.utc)-timedelta(days=2)
except Exception:
    previous_visit = datetime.now(timezone.utc)-timedelta(days=2)

def event_dt(e):
    try:return date.fromisoformat(e.start_date)
    except Exception:return date.max

def is_new(e):
    try:return bool(e.created_at and datetime.fromisoformat(e.created_at)>previous_visit)
    except Exception:return False

def fmt_date(d):
    months=["jan","feb","mar","apr","maj","jun","jul","aug","sep","okt","nov","dec"]
    return f"{d.day} {months[d.month-1]} {d.year}"

future_events=[e for e in events if event_dt(e)>=today]
fav_ids=favorite_ids()

st.markdown("""<div class="hero"><div class="eyebrow">UPPLEVIO · EVENEMANGSRADAR</div>
<h1>Hitta det du<br>inte vill missa.</h1>
<p>Konserter, mässor och större evenemang från flera källor – samlade, verifierade och enkla att skanna.</p></div>""",unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### Filtrera")
    query=st.text_input("Sök",placeholder="Artist, mässa, arena eller ort…")
    types=["Alla"]+sorted({e.event_type for e in future_events})
    type_filter=st.selectbox("Typ",types)
    collector_mode=st.toggle("Samlarvärlden", value=False, help="Fokusera på samlarkort, sportkort, Pokémon/TCG, retro, gaming, comics, Lego och närliggande mässor.")
    collector_sub=st.selectbox("Samlarinriktning", collector_subcategories(), disabled=not collector_mode)
    cities=sorted({e.city for e in future_events if e.city})
    city_filter=st.multiselect("Orter",cities)
    period=st.selectbox("När",["Nästa 30 dagar","Nästa 3 månader","Nästa 6 månader","Nästa 12 månader","Alla kommande"])
    only_new=st.toggle("Endast nytt sedan sist")
    only_favorites=st.toggle("Endast sparade")
    hide_demo=st.toggle("Dölj demodata", value=False)
    st.markdown("#### Avstånd")
    origin_city=st.selectbox("Utgå från", ["Ingen"]+sorted(CITY_COORDS.keys()))
    radius_km=st.selectbox("Radie", [25,50,100,200,300], index=2, disabled=(origin_city=="Ingen"))
    st.markdown("#### Intressen")
    interest_options = sorted({
         "Rock","Hårdrock/metal","Pop","Hip-hop","Jazz","Elektroniskt","Stand-up",
        "Teknik","Industri","Miljö & hållbarhet","Samlarkort","Sportkort",
        "Retro & nostalgi","Gaming","Fordon","Mat & dryck","Sport","Comic/anime","Lego","Festival"
    })
    user_interests = set(st.multiselect(
        "Prioritera",
        interest_options,
        default=[x for x in interest_options if x in DEFAULT_INTERESTS],
        help="Används bara för sortering och Upptäck. Det filtrerar inte bort andra event."
    ))

days_map={"Nästa 30 dagar":30,"Nästa 3 månader":92,"Nästa 6 månader":183,"Nästa 12 månader":365}
cutoff=today+timedelta(days=days_map.get(period,3650))

def matches(e):
    if event_dt(e)>cutoff:return False
    if type_filter!="Alla" and e.event_type!=type_filter:return False
    if collector_mode and not collector_match(e, collector_sub):return False
    if city_filter and e.city not in city_filter:return False
    if only_new and not is_new(e):return False
    if only_favorites and e.id not in fav_ids:return False
    if hide_demo and e.is_demo:return False
    if origin_city!="Ingen":
        dist=distance_from_city(e,origin_city)
        if dist is None or dist>radius_km:return False
    if query:
        hay=" ".join([e.title,e.event_type,e.category,e.venue,e.city,e.region,e.description,*e.tags]).lower()
        if query.lower() not in hay:return False
    return True

filtered=sorted([e for e in future_events if matches(e)],key=event_dt)
new_count=sum(is_new(e) for e in filtered)
next30=sum(event_dt(e)<=today+timedelta(days=30) for e in filtered)
multi_source=sum(e.source_count>1 for e in filtered)

st.markdown(f"""<div class="metric-grid">
<div class="metric-card"><div class="metric-n">{len(filtered)}</div><div class="metric-l">Kommande</div></div>
<div class="metric-card"><div class="metric-n">{new_count}</div><div class="metric-l">Nya sedan sist</div></div>
<div class="metric-card"><div class="metric-n">{next30}</div><div class="metric-l">Nästa 30 dagar</div></div>
<div class="metric-card"><div class="metric-n">{multi_source}</div><div class="metric-l">Bekräftade av flera källor</div></div>
</div>""",unsafe_allow_html=True)

# 7-day pulse
st.markdown('<div class="section-title">Nästa 7 dagar</div>',unsafe_allow_html=True)
daycols=st.columns(7)
weekday=["Mån","Tis","Ons","Tor","Fre","Lör","Sön"]
for i,c in enumerate(daycols):
    d=today+timedelta(days=i)
    n=sum(event_dt(e)==d for e in filtered)
    with c:
        st.markdown(f'<div class="day-card"><div class="eyebrow">{weekday[d.weekday()]}</div><div class="day-n">{n}</div><div class="source">{d.day}/{d.month}</div></div>',unsafe_allow_html=True)


def discovery_card(e, label=None, reason=None, distance=None):
    badges = f'<span class="badge">{e.event_type}</span><span class="badge">{e.category}</span>'
    if label:
        badges = f'<span class="badge badge-new">{label}</span>' + badges
    dist_line = f"<br>{distance} km bort" if distance is not None else ""
    reason_html = f'<div class="source">{reason}</div>' if reason else ""
    return f"""<div class="event-card">{badges}
    <div class="event-title">{e.title}</div>
    <div class="event-meta">{fmt_date(event_dt(e))}<br>{e.venue or "Plats ej angiven"} · {e.city or "Ort saknas"}{dist_line}</div>
    {reason_html}</div>"""

tab_radar,tab_discover,tab_watches,tab_list,tab_saved,tab_admin=st.tabs(["Radar","Upptäck","Bevakningar","Listvy","Mina evenemang","Admin / datakvalitet"])

with tab_radar:
    if new_count:
        st.markdown('<div class="section-title">Nytt sedan sist</div>',unsafe_allow_html=True)
        new_events=[e for e in filtered if is_new(e)][:6]
        ncols=st.columns(3)
        for idx,e in enumerate(new_events):
            with ncols[idx%3]:
                st.markdown(f"""<div class="event-card">
                <span class="badge badge-new">NY</span><span class="badge">{e.event_type}</span>
                <div class="event-title">{e.title}</div>
                <div class="event-meta">{fmt_date(event_dt(e))}<br>{e.venue or "Plats ej angiven"} · {e.city or "Ort saknas"}</div>
                <div class="source">{", ".join(e.source_names)}</div></div>""",unsafe_allow_html=True)

    st.markdown('<div class="section-title">Alla matchningar</div>',unsafe_allow_html=True)
    if not filtered: st.info("Inga evenemang matchar filtren.")
    cols=st.columns(3)
    for idx,e in enumerate(filtered):
        with cols[idx%3]:
            qbadge='<span class="badge badge-review">BEHÖVER GRANSKAS</span>' if e.data_quality=="review" else ""
            dist=distance_from_city(e,origin_city) if origin_city!="Ingen" else None
            distance_line=f"<br>{dist} km från {origin_city}" if dist is not None else ""
            demo='<span class="badge">DEMO</span>' if e.is_demo else ""
            new='<span class="badge badge-new">NY</span>' if is_new(e) else ""
            st.markdown(f"""<div class="event-card">{new}<span class="badge">{e.event_type}</span><span class="badge">{e.category}</span>{demo}{qbadge}
            <div class="event-title">{e.title}</div>
            <div class="event-meta">{fmt_date(event_dt(e))}<br>{e.venue or "Plats ej angiven"} · {e.city or "Ort saknas"}{distance_line}<br>{e.status}</div>
            <div class="source">{e.source_count} källa/källor · {", ".join(e.source_names)}</div></div>""",unsafe_allow_html=True)
            b1,b2=st.columns(2)
            if b1.button("Detaljer",key=f"d-{e.id}",use_container_width=True):st.session_state["selected_event"]=e.id
            label="♥ Sparad" if e.id in fav_ids else "♡ Spara"
            if b2.button(label,key=f"f-{e.id}",use_container_width=True):
                toggle_favorite(e.id);st.rerun()

    selected=next((e for e in events if e.id==st.session_state.get("selected_event")),None)
    if selected:
        st.markdown('<div class="section-title">Evenemangsdetalj</div>',unsafe_allow_html=True)
        st.markdown(f"""<div class="detail-box"><div class="eyebrow">{selected.event_type} · {selected.category}</div>
        <div class="event-title" style="font-size:2rem">{selected.title}</div>
        <div class="event-meta"><b>Datum:</b> {selected.start_date}{(" · "+selected.start_time) if selected.start_time else ""}<br>
        <b>Plats:</b> {selected.venue or "Ej angiven"}, {selected.city or "Ort saknas"}<br>
        <b>Källor:</b> {", ".join(selected.source_names)}<br>
        <b>Senast verifierad:</b> {selected.verified_at or "okänt"}<br>
        <b>Datakvalitet:</b> {selected.data_quality}</div><p>{selected.description or "Ingen beskrivning tillgänglig."}</p></div>""",unsafe_allow_html=True)
        if selected.quality_notes:
            for note in selected.quality_notes: st.caption("• "+note)
        if selected.official_url:st.link_button("Officiell sida",selected.official_url)


with tab_discover:
    st.markdown('<div class="section-title">Upptäck</div>', unsafe_allow_html=True)
    st.caption("Här prioriteras sådant som verkar extra relevant. Reglerna är transparenta och kan justeras senare.")

    # Recommended
    recommended = recommended_for_you(filtered, user_interests, limit=9)
    st.markdown("### Rekommenderat för dig")
    if not recommended:
        st.info("Välj några intressen för att få rekommendationer.")
    else:
        cols = st.columns(3)
        for i,(score,e,reasons) in enumerate(recommended):
            with cols[i % 3]:
                reason = " · ".join(reasons[:2]) if reasons else "Matchar dina val"
                st.markdown(discovery_card(e, "MATCH", reason), unsafe_allow_html=True)

    # Worth a trip
    travel_origin = origin_city if origin_city != "Ingen" else "Örebro"
    travel = worth_a_trip(future_events, travel_origin, user_interests, limit=6)
    st.markdown(f"### Värt en resa från {travel_origin}")
    if not travel:
        st.info("Inga tydliga resekandidater just nu.")
    else:
        cols = st.columns(3)
        for i,(score,e,reasons,dist) in enumerate(travel):
            with cols[i % 3]:
                reason = " · ".join(reasons[:3])
                st.markdown(discovery_card(e, "VÄRT EN RESA", reason, dist), unsafe_allow_html=True)

    # Newly announced
    new_rows = newly_announced(future_events, is_new, limit=9)
    st.markdown("### Nyannonserat")
    if not new_rows:
        st.caption("Inget nytt sedan senaste registrerade besöket.")
    else:
        cols = st.columns(3)
        for i,e in enumerate(new_rows):
            with cols[i % 3]:
                st.markdown(discovery_card(e, "NY", ", ".join(e.source_names)), unsafe_allow_html=True)

    # Weekend
    weekend_rows = this_weekend(future_events)
    st.markdown("### Kommande helg")
    if not weekend_rows:
        st.caption("Inga kända event i datan för kommande lördag/söndag.")
    else:
        cols = st.columns(3)
        for i,e in enumerate(weekend_rows[:9]):
            with cols[i % 3]:
                st.markdown(discovery_card(e, "HELG"), unsafe_allow_html=True)


    # Collector world
    collector_rows = [e for e in future_events if collector_match(e, "Alla samlare")]
    collector_rows = sorted(collector_rows, key=event_dt)[:9]
    st.markdown("### Samlarvärlden")
    st.caption("Samlarkort, sportkort, Pokémon/TCG, retro, gaming, comics, Lego och närliggande samlarmässor.")
    if not collector_rows:
        st.caption("Inga samlarevent i aktuell datamängd ännu. Aktivera experimentella samlarkällor i sidopanelen när de ska testas.")
    else:
        cols=st.columns(3)
        for i,e in enumerate(collector_rows):
            with cols[i % 3]:
                collector_tags=[t for t in e.tags if t in {"Samlarkort","Sportkort","Retro & nostalgi","Gaming","Comic/anime","Lego","Leksaker"}]
                reason=" · ".join(collector_tags[:3]) or e.category
                st.markdown(discovery_card(e,"SAMLA",reason),unsafe_allow_html=True)

    # Big fairs
    fairs = big_fairs(future_events, limit=6)
    st.markdown("### Stora mässor framåt")
    if not fairs:
        st.caption("För få verifierade mässor för en bra topplista ännu.")
    else:
        cols = st.columns(3)
        for i,(score,e,reasons) in enumerate(fairs):
            with cols[i % 3]:
                reason = " · ".join(reasons[:2]) if reasons else "Prioriterad mässa"
                st.markdown(discovery_card(e, "MÄSSA", reason), unsafe_allow_html=True)



with tab_watches:
    st.markdown('<div class="section-title">Bevakningar</div>', unsafe_allow_html=True)
    st.caption("Spara det du vill hålla koll på. Notifieringar kopplas på senare; reglerna lagras separat från eventen.")
    c1,c2=st.columns([2,1])
    with c1:
        wn=st.text_input("Namn",placeholder="Samlarkort inom 200 km")
        wq=st.text_input("Sökord",placeholder="RetroMania, Pokémon, Johan Glans")
        wt=st.selectbox("Evenemangstyp",["Alla","Stand-up","Mässa","Konsert","Festival","Teater","Show","Evenemang"],key="watch-type")
        wc=st.selectbox("Kategori",["Alla","Samlarkort","Sportkort","Retro & nostalgi","Gaming","Comic/anime","Lego","Stand-up"],key="watch-cat")
    with c2:
        wo=st.selectbox("Utgångsort",["Ingen"]+sorted(CITY_COORDS.keys()),key="watch-origin")
        wr=st.selectbox("Radie km",[25,50,100,200,300],index=3,disabled=(wo=="Ingen"),key="watch-radius")
        if st.button("Spara bevakning",type="primary",use_container_width=True):
            add_watch(wn or "Min bevakning",query=wq,event_type="" if wt=="Alla" else wt,category="" if wc=="Alla" else wc,origin_city="" if wo=="Ingen" else wo,radius_km=None if wo=="Ingen" else wr); st.rerun()
    watches=list_watches()
    if not watches: st.info("Du har inga sparade bevakningar ännu.")
    else:
        st.markdown("### Sparade bevakningar")
        for w in watches:
            terms=[]
            if w["query"]: terms.append(f'sökord: {w["query"]}')
            if w["event_type"]: terms.append(w["event_type"])
            if w["category"]: terms.append(w["category"])
            if w["origin_city"]: terms.append(f'{w["radius_km"]} km från {w["origin_city"]}')
            a,b=st.columns([5,1])
            with a:
                st.markdown(f"**{w['name']}**"); st.caption(" · ".join(terms) if terms else "Alla evenemang")
            with b:
                if st.button("Ta bort",key=f"watch-del-{w['id']}"):
                    delete_watch(w["id"]); st.rerun()

with tab_list:
    rows=[{"Datum":e.start_date,"Evenemang":e.title,"Typ":e.event_type,"Kategori":e.category,"Ort":e.city,"Arena":e.venue,"Källor":e.source_count,"Ny":"Ja" if is_new(e) else ""} for e in filtered]
    st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)

with tab_saved:
    saved=[e for e in future_events if e.id in fav_ids]
    if not saved:st.info("Du har inte sparat några evenemang ännu.")
    for e in sorted(saved,key=event_dt):st.write(f"**{e.title}** — {fmt_date(event_dt(e))} · {e.city} · {e.venue}")

with tab_admin:
    st.markdown("### Källstatus")
    health=pd.DataFrame(source_health,columns=["Källa","Status","Importerade","Kommentar"])
    st.dataframe(health,use_container_width=True,hide_index=True)
    st.markdown("### Möjliga dubletter")
    if not review_pairs:st.success("Inga tveksamma dublettkandidater i aktuell import.")
    else:
        review_rows=[]
        for a,b,score in review_pairs:
            review_rows.append({"A":a.title,"B":b.title,"Datum":a.start_date,"Ort":a.city or b.city,"Likhet":f"{score:.0%}","Källa A":", ".join(a.source_names),"Källa B":", ".join(b.source_names)})
        st.dataframe(pd.DataFrame(review_rows),use_container_width=True,hide_index=True)
    st.markdown("### Källregister")
    registry_rows=[{
        "Källa":x.name,
        "Typ":x.source_type,
        "Täcker":x.coverage,
        "Ort":x.city or "Nationellt",
        "Tillitsnivå":x.trust_level,
        "Import":x.import_mode,
        "Standard": "På" if x.enabled_by_default else "Av",
        "Kommentar":x.notes
    } for x in SOURCES]
    st.dataframe(pd.DataFrame(registry_rows),use_container_width=True,hide_index=True)
    st.caption("Officiella HTML-källor är registrerade men avstängda som standard tills parsern verifierats mot verklig drift.")
    st.markdown("### Princip")
    st.write("Automatisk sammanslagning sker bara vid hög säkerhet. Osäkra kandidater visas här för manuell kontroll i stället för att appen chansar.")
    st.caption(f"Råposter: {len(raw_events)} · kanoniska event: {len(events)} · granskningskandidater: {len(review_pairs)}")

set_meta("last_visit",datetime.now(timezone.utc).isoformat())
st.caption("Upplevio v0.7.0 · Upptäck mer. Upplev mer.")
