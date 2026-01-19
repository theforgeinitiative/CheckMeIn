<%def name="scripts()">
<script>
// Pagination: show one page at a time with a 15s timer progress bar
const PAGE_SECONDS = 10;
let pageIndex = 0;
let pageTimer = null;
let progressTimer = null;

// Data from server (pre-serialized JSON)
function getToolsData(){
  const el = document.getElementById('tools-json');
  if(!el) return [];
  try { return JSON.parse(el.textContent || '[]'); } catch(e){ return []; }
}
let toolsData = [];

function renderPage(idx){
  const container = document.getElementById('cards-grid');
  if(!container) return;
  const pageSize = 5; // exactly 5 tools per page
  const start = (idx * pageSize) % toolsData.length;
  const slice = toolsData.slice(start, start + pageSize);
  const items = slice.length < pageSize ? slice.concat(toolsData.slice(0, pageSize - slice.length)) : slice;
  var html = '';
  items.forEach(function(tool){
    var sources = '';
    if (tool.image_url) { sources += '<source srcset="' + tool.image_url + '" type="image/avif"/>'; }
    if (tool.img_avif)  { sources += '<source srcset="' + tool.img_avif  + '" type="image/avif"/>'; }
    if (tool.img_png)   { sources += '<source srcset="' + tool.img_png   + '" type="image/png"/>'; }
    if (tool.img_jpg)   { sources += '<source srcset="' + tool.img_jpg   + '" type="image/jpeg"/>'; }
    var imgSrc = tool.img_png || tool.img_jpg || tool.image_url || '/static/tools/placeholder.svg';
    var membersHtml = '';
    if (!tool.members || tool.members.length === 0) {
      membersHtml = "<div class='member' style='color:var(--muted)'>No certified members</div>";
    } else {
      for (var i=0;i<tool.members.length;i++){
        var m = tool.members[i];
        membersHtml += "<div class='member level-" + m.level + "'>" +
                       "<div class='name'>" + m.displayName + "</div>" +
                       "<div class='level-chip level-" + m.level + "'>" + m.level_name + "</div>" +
                       "</div>";
      }
    }
    html += '<div class="card">' +
              '<div class="card-top">' +
                '<picture class="tool-hero">' + sources +
                  '<img class="tool-hero" src="' + imgSrc + '" alt="' + tool.name + '" onerror="this.onerror=null; this.src=\'/static/tools/placeholder.svg\';"/>' +
                '</picture>' +
                '<div class="card-header">' +
                  '<div class="card-title">' + tool.name + '</div>' +
                '</div>' +
              '</div>' +
              '<div class="card-body">' +
                membersHtml +
              '</div>' +
            '</div>';
  });
  container.innerHTML = html;
}

function startPagination(){
  const bar = document.getElementById('progress-bar');
  const inner = document.getElementById('progress-inner');
  // Load tools data now that DOM is ready
  toolsData = getToolsData();
  function tick(){
    // advance page
    pageIndex = (pageIndex + 1) % Math.ceil(toolsData.length / 5);
    renderPage(pageIndex);
    // restart progress
    inner.style.transition = 'none';
    inner.style.width = '0%';
    requestAnimationFrame(function(){
      requestAnimationFrame(function(){
        inner.style.transition = 'width ' + PAGE_SECONDS + 's linear';
        inner.style.width = '100%';
      });
    });
  }
  // initial render and animate
  renderPage(pageIndex);
  inner.style.transition = 'width ' + PAGE_SECONDS + 's linear';
  inner.style.width = '100%';
  if(pageTimer) clearInterval(pageTimer);
  pageTimer = setInterval(tick, PAGE_SECONDS * 1000);
}

window.addEventListener('load', startPagination);

// Live clock in header (right side)
function updateClock(){
  const el = document.getElementById('cm-clock');
  if(!el) return;
  const now = new Date();
  el.textContent = now.toLocaleString();
}
setInterval(updateClock, 1000);
window.addEventListener('load', updateClock);
</script>
</%def>
<%def name="head()">
<style>
:root{ --c10:#0e7490; --c20:#166534; --c30:#92400e; --c40:#7f1d1d; --card:#0b1220; --text:#e5e7eb; --muted:#94a3b8; --bg:#0a0f1a; --border:#1f2937; --accent:#60a5fa; --basic:#ef4444; --certified:#22c55e; --dof:#eab308; --instructor:#3b82f6; --certifier:#9ca3af; }
body{ font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif; background: var(--bg); color: var(--text); }
/* Member row accents per level */
.member.level-1{ background: rgba(239,68,68,.12); border-left:4px solid var(--basic); }
.member.level-10{ background: rgba(34,197,94,.12); border-left:4px solid var(--certified); }
.member.level-20{ background: rgba(234,179,8,.12); border-left:4px solid var(--dof); }
.member.level-30{ background: rgba(59,130,246,.12); border-left:4px solid var(--instructor); }
.member.level-40{ background: rgba(156,163,175,.12); border-left:4px solid var(--certifier); }
.grid{ display:grid; grid-template-columns: repeat(1, minmax(0, 1fr)); gap:16px; }
@media(min-width:640px){ .grid{ grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media(min-width:900px){ .grid{ grid-template-columns: repeat(3, minmax(0, 1fr)); } }
@media(min-width:1200px){ .grid{ grid-template-columns: repeat(4, minmax(0, 1fr)); } }
@media(min-width:1440px){ .grid{ grid-template-columns: repeat(5, minmax(0, 1fr)); } }
.card{ background:var(--card); border-radius:12px; box-shadow: 0 2px 12px rgba(0,0,0,.4); border:1px solid var(--border); overflow:hidden; display:flex; flex-direction:column; }
.card-top{ position:sticky; top:0; z-index:1; background: var(--card); border-bottom:1px solid var(--border); }
.card-header{ display:flex; align-items:center; justify-content:center; gap:12px; padding:12px 14px; }
.card-title{ font-weight:700; color:var(--text); font-size:24px; text-align:center; width:100%; }
.tool-hero{ width:100%; height:200px; object-fit:contain; background:#0b1220; border-bottom:1px solid var(--border); }
.card-body{ padding:10px 14px; display:flex; flex-direction:column; gap:8px; }
.member{ display:flex; align-items:center; justify-content:space-between; padding:6px 8px; border-radius:8px; }
.name{ font-size:14px; color:var(--text); font-weight:500; }
.level-chip{ font-size:12px; padding:2px 8px; border-radius:9999px; border:1px solid var(--border); color:#0a0a0a; background:#e5e7eb; }
/* Chips per level */
.level-chip.level-1{ background: var(--basic); }
.level-chip.level-10{ background: var(--certified); }
.level-chip.level-20{ background: var(--dof); }
.level-chip.level-30{ background: var(--instructor); }
.level-chip.level-40{ background: var(--certifier); }
#cards-container{ max-height: calc(100vh - 160px); overflow:hidden; padding-right:6px; }
.header{ display:flex; align-items:center; justify-content:space-between; gap:12px; flex-wrap:wrap; margin: 6px 0 10px; }
.masthead{ display:grid; grid-template-columns: 1fr auto 1fr; align-items:center; gap:12px; margin: 6px 0 6px; }
.masthead .left{ justify-self:start; }
.masthead .center{ justify-self:center; }
.masthead .right{ justify-self:end; }
.title{ font-size:40px; font-weight:700; color: var(--text); }
.clock{ color: var(--muted); font-size: 28px; }
.progress { height: 6px; width: 100%; background: #111827; border-radius: 9999px; overflow: hidden; border:1px solid var(--border); }
.progress > .bar { height: 100%; width: 0%; background: var(--accent); }
.logo-bar{ display:flex; align-items:center; justify-content:center; padding:0; }
.logo-bar img{ max-height:80px; width:auto; opacity:.9; }
</style>
</%def>

<%def name="title()">Certification Monitor</%def>
<%inherit file="base.mako"/>

<div class="masthead">
  <div class="left title">Certification Monitor</div>
  <div class="center logo-bar">
    <img src="https://photos.smugmug.com/Logos/TFD-TFI-TUF-Logos/i-dDKzxPw/0/NcCVLCWrFZQczNXLvBsB4qgHDSC7bxX4P8mSH7DS3/XL/TFI%20logo%20BLACK%20high%20quality%20no%20tagline-XL.jpg" alt="TFI logo" />
  </div>
  <div class="right clock" id="cm-clock"></div>
  </div>

<div id="cards-container">
  <script id="tools-json" type="application/json">${ (tools_json if tools_json is not UNDEFINED else '[]') | n }</script>
  <div class="progress" id="progress-bar"><div class="bar" id="progress-inner"></div></div>
  <div class="grid" id="cards-grid"></div>
</div>
