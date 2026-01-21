<%def name="scripts()">
<script>
// ===== FEATURE FLAGS =====
const ENABLE_RESOURCE_PAGE = false;  // Set to false to disable resource page
const SCROLL_CYCLES_BEFORE_RESOURCE = 1;  // Show resource page every N full scrolls (1 = every time)

// ===== AUTO-SCROLL CONFIGURATION =====
const SCROLL_SPEED = 30; // pixels per second for certification grid
const PAUSE_DURATION = 1; // milliseconds to pause when new row enters view
const ROW_HEIGHT = 50; // approximate height of one row in pixels
const RESOURCE_PAGE_DURATION = 12000; // milliseconds to show resource page
const RESOURCE_SCROLL_SPEED = 40; // pixels per second for resource page (no pauses, so can be faster)
const RESTART_PAUSE = 2000; // pause before restarting scroll cycle

// ===== STATE VARIABLES =====
let scrollPosition = 0;
let resourceScrollPosition = 0;
let isPaused = false;
let lastRowCrossed = 0;
let isShowingResourcePage = false;
let hasCompletedCycle = false;
let completedCycleCount = 0;
let contentDuplicated = false;

function smoothScroll() {
    if (isPaused || isShowingResourcePage) return;
    
    const tableBody = document.getElementById('scrolling-body');
    const container = document.querySelector('.table-container');
    
    if (!tableBody || !container) return;
    
    // Duplicate content for seamless looping (only once)
    if (!contentDuplicated) {
        const rows = Array.from(tableBody.querySelectorAll('tr'));
        rows.forEach(row => {
            const clone = row.cloneNode(true);
            tableBody.appendChild(clone);
        });
        contentDuplicated = true;
    }
    
    // Calculate scroll boundaries
    const singleSetHeight = tableBody.offsetHeight / 2; // Height of original content (before duplication)
    
    if (singleSetHeight <= container.offsetHeight) {
        // Content fits on screen, handle resource page
        if (!hasCompletedCycle && ENABLE_RESOURCE_PAGE) {
            hasCompletedCycle = true;
            completedCycleCount++;
            if (completedCycleCount >= SCROLL_CYCLES_BEFORE_RESOURCE) {
                setTimeout(showResourcePage, PAUSE_DURATION * 2);
            } else {
                hasCompletedCycle = false;
            }
        }
        return;
    }
    
    // Increment scroll position
    scrollPosition += SCROLL_SPEED / 60;
    
    // Check if we have crossed into a new row
    const currentRow = Math.floor(scrollPosition / ROW_HEIGHT);
    if (currentRow > lastRowCrossed) {
        lastRowCrossed = currentRow;
        isPaused = true;
        setTimeout(() => {
            isPaused = false;
        }, PAUSE_DURATION);
    }
    
    // Seamless loop: when we have scrolled through one complete set, jump back to start
    // The duplicate content is now visible, so the jump is invisible
    if (scrollPosition >= singleSetHeight) {
        // Mark that we have completed a cycle
        completedCycleCount++;
        
        // Reset to start (seamlessly)
        scrollPosition = 0;
        lastRowCrossed = 0;
        container.scrollTop = 0;
        
        // Check if we should show resource page
        if (ENABLE_RESOURCE_PAGE && completedCycleCount >= SCROLL_CYCLES_BEFORE_RESOURCE) {
            hasCompletedCycle = true;
            isPaused = true;
            setTimeout(showResourcePage, RESTART_PAUSE);
        }
        return;
    }
    
    container.scrollTop = scrollPosition;
}

function smoothScrollResourcePage() {
    if (!isShowingResourcePage) return;
    
    const container = document.getElementById('resource-page');
    if (!container) return;
    
    // Calculate total scrollable height
    const maxScroll = container.scrollHeight - container.clientHeight;
    
    if (maxScroll <= 0) {
        // Content fits on screen, no scrolling needed
        return;
    }
    
    // Increment scroll position (continuous, no pauses)
    resourceScrollPosition += RESOURCE_SCROLL_SPEED / 60;
    
    // Loop back to top when we reach the end
    if (resourceScrollPosition >= maxScroll) {
        resourceScrollPosition = 0;
    }
    
    container.scrollTop = resourceScrollPosition;
}

function showResourcePage() {
    isShowingResourcePage = true;
    completedCycleCount = 0; // Reset the cycle counter
    
    // Save current scroll position before switching
    sessionStorage.setItem('certScrollBeforeResource', scrollPosition.toString());
    
    document.querySelector('.table-container').style.display = 'none';
    document.getElementById('resource-page').style.display = 'block';
    
    // Resume from where we left off
    document.getElementById('resource-page').scrollTop = resourceScrollPosition;
    
    // Return to grid after duration
    setTimeout(hideResourcePage, RESOURCE_PAGE_DURATION);
}

function hideResourcePage() {
    isShowingResourcePage = false;
    hasCompletedCycle = false;
    // Do not reset resourceScrollPosition - it will continue from here next time
    
    document.getElementById('resource-page').style.display = 'none';
    document.querySelector('.table-container').style.display = 'block';
    
    // Restore the cylinder position (do not reset to 0)
    const savedPosition = sessionStorage.getItem('certScrollBeforeResource');
    if (savedPosition !== null) {
        scrollPosition = parseFloat(savedPosition);
        document.querySelector('.table-container').scrollTop = scrollPosition;
    }
    
    // Pause briefly, then resume scrolling
    isPaused = true;
    setTimeout(() => {
        isPaused = false;
    }, RESTART_PAUSE);
}

// Save scroll position before page unload
window.addEventListener('beforeunload', () => {
    sessionStorage.setItem('certScrollPosition', scrollPosition.toString());
    sessionStorage.setItem('certCompletedCycles', completedCycleCount.toString());
    sessionStorage.setItem('certResourceScrollPosition', resourceScrollPosition.toString());
    sessionStorage.setItem('certIsShowingResourcePage', isShowingResourcePage.toString());
});

// Start scrolling when page loads
window.addEventListener('load', () => {
    // Restore saved state if it exists
    const savedScroll = sessionStorage.getItem('certScrollPosition');
    const savedCycles = sessionStorage.getItem('certCompletedCycles');
    const savedResourceScroll = sessionStorage.getItem('certResourceScrollPosition');
    const savedShowingResource = sessionStorage.getItem('certIsShowingResourcePage');
    
    if (savedScroll !== null) {
        scrollPosition = parseFloat(savedScroll);
    }
    
    if (savedCycles !== null) {
        completedCycleCount = parseInt(savedCycles);
    }
    
    if (savedResourceScroll !== null) {
        resourceScrollPosition = parseFloat(savedResourceScroll);
    }
    
    // If we were showing resource page when reload happened, show it again
    if (savedShowingResource === 'true') {
        showResourcePage();
    } else {
        // Restore scroll position for certification grid
        if (savedScroll !== null) {
            // Wait for content duplication to happen first
            setTimeout(() => {
                document.querySelector('.table-container').scrollTop = scrollPosition;
            }, 100);
        }
    }
    
    // Start scrolling
    setInterval(() => {
        smoothScroll();
        smoothScrollResourcePage();
    }, 1000 / 60);
});
</script>

<style>
.table-container {
    height: calc(100vh - 20px);
    overflow: hidden;
    position: relative;
}

.certifications {
    width: 100%;
    border-collapse: collapse;
}

.certifications thead {
    position: sticky;
    top: 0;
    background: #1a1a1a;
    z-index: 10;
    box-shadow: 0 2px 4px rgba(0,0,0,0.3);
}

.certifications th {
    padding: 8px 4px;
    font-size: 1.0vw;
    font-weight: bold;
    border: 2px solid #333;
    white-space: wrap;
}

.certifications td {
    padding: 6px 4px;
    font-size: 1.2em;
    border: 1px solid #444;
    text-align: center;
}

.certifications td.user-name {
    font-weight: bold;
    font-size: 1.0vw;
    position: sticky;
    background: inherit;
}

.certifications td.user-name.left {
    left: 0;
    z-index: 5;
}

.certifications td.user-name.right {
    right: 0;
    z-index: 5;
}

/* Certification cell font sizes */
.certifications td.clNone,
.certifications td.clBasic,
.certifications td.clCertified,
.certifications td.clDOF,
.certifications td.clInstructor,
.certifications td.clCertifier {
    font-size: 1.0vw !important;
}

/* Resource Page Styles */
#resource-page {
    display: none;
    height: calc(100vh - 20px);
    overflow-y: auto;
    overflow-x: hidden;
    background: #1a1a1a;
    padding: 20px;
    scroll-behavior: smooth;
}

/* Hide scrollbar for resource page but keep functionality */
#resource-page::-webkit-scrollbar {
    display: none;
}

#resource-page {
    -ms-overflow-style: none;  /* IE and Edge */
    scrollbar-width: none;  /* Firefox */
}

#resource-page h1 {
    text-align: center;
    font-size: 2.5em;
    margin: 20px 0 40px 0;
    border-bottom: 4px solid #444;
    padding-bottom: 20px;
    color: #fff;
}

.tool-help-section {
    margin-bottom: 25px;
    padding: 15px;
    background: #2a2a2a;
    border-radius: 8px;
    border-left: 5px solid #555;
}

.tool-name {
    font-size: 1.8em;
    font-weight: bold;
    color: #fff;
    margin-bottom: 10px;
}

.helper-group {
    margin: 8px 0;
    font-size: 1.4em;
}

.helper-label {
    display: inline-block;
    width: 200px;
    font-weight: bold;
}

.helper-label.dof {
    color: #ff9933; /* Orange for DoF */
}

.helper-label.instructor {
    color: #4da6ff; /* Blue for Instructor */
}

.helper-label.certifier {
    color: #999; /* Grey for Certifier */
}

.helper-names {
    display: inline;
    color: #ddd;
}

.no-helpers {
    color: #666;
    font-style: italic;
}

/* Two-column layout for resource page on wide screens */
@media (min-width: 1400px) {
    .tools-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 20px;
    }
}

/* Gradient hint at bottom of resource page */
#resource-page::after {
    content: '';
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    height: 60px;
    background: linear-gradient(to bottom, transparent, rgba(0,0,0,0.8));
    pointer-events: none;
}
</style>
</%def>

<%def name="head()">
<meta http-equiv="refresh" content="60">
</%def>

<%def name="title()">Certifications</%def>
<%inherit file="base.mako"/>

% if message:
<H1>${message}</H1>
% endif

<!-- Main Certification Grid -->
<div class="table-container">
    <table class="certifications">
        <thead>
            <tr>
                % if show_left_names:
                <th class="name-column">Name</th>
                % endif
                % for tool in tools:
                <th>${tool[1]}</th>
                % endfor
                % if show_right_names:
                <th class="name-column">Name</th>
                % endif
            </tr>
        </thead>
        <tbody id="scrolling-body">
            % for user, user_tools in certifications.items():
            <tr>
                % if show_left_names:
                <td class="user-name left">${user_tools.displayName}</td>
                % endif
                % for tool in tools:
                ${user_tools.getHTMLCellTool(tool[0]) | n}
                % endfor
                % if show_right_names:
                <td class="user-name right">${user_tools.displayName}</td>
                % endif
            </tr>
            % endfor
        </tbody>
    </table>
</div>

<!-- Resource Page: Who Can Help -->
<div id="resource-page">
    <h1>WHO CAN HELP YOU RIGHT NOW</h1>
    
    <div class="tools-grid">
    <%
        # Import the CertificationLevels enum
        from certifications import CertificationLevels
        
        # Build helper data structure
        # This organizes users by their certification level on each tool
        tool_helpers = {}
        for tool in tools:
            tool_id = tool[0]
            tool_name = tool[1]
            tool_helpers[tool_id] = {
                'name': tool_name,
                'dof': [],
                'instructor': [],
                'certifier': []
            }
        
        # Iterate through all present users and categorize them
        for user, user_tools in certifications.items():
            for tool in tools:
                tool_id = tool[0]
                # Get the certification tuple (date, level)
                date, level = user_tools.getTool(tool_id)
                
                # Categorize by level
                if level == CertificationLevels.DOF:
                    tool_helpers[tool_id]['dof'].append(user_tools.displayName)
                elif level == CertificationLevels.INSTRUCTOR:
                    tool_helpers[tool_id]['instructor'].append(user_tools.displayName)
                elif level == CertificationLevels.CERTIFIER:
                    tool_helpers[tool_id]['certifier'].append(user_tools.displayName)
    %>
    
    % for tool in tools:
    <%
        tool_id = tool[0]
        tool_name = tool[1]
    %>
        <div class="tool-help-section">
            <div class="tool-name">${tool_name}</div>
            
            <div class="helper-group">
                <span class="helper-label dof">Defenders of Fingers:</span>
                % if tool_helpers[tool_id]['dof']:
                    <span class="helper-names">${', '.join(tool_helpers[tool_id]['dof'])}</span>
                % else:
                    <span class="no-helpers">None available</span>
                % endif
            </div>
            
            <div class="helper-group">
                <span class="helper-label instructor">Instructors:</span>
                % if tool_helpers[tool_id]['instructor']:
                    <span class="helper-names">${', '.join(tool_helpers[tool_id]['instructor'])}</span>
                % else:
                    <span class="no-helpers">None available</span>
                % endif
            </div>
            
            <div class="helper-group">
                <span class="helper-label certifier">Certifiers:</span>
                % if tool_helpers[tool_id]['certifier']:
                    <span class="helper-names">${', '.join(tool_helpers[tool_id]['certifier'])}</span>
                % else:
                    <span class="no-helpers">None available</span>
                % endif
            </div>
        </div>
    % endfor
    </div>
</div>
