<%def name="scripts()">
<script src="https://code.jquery.com/ui/1.12.1/jquery-ui.js"></script>
<script>
function deactivateTeam(teamName, team_id) {
		if (confirm("OK to deactivate team " + teamName + "?")) {
			window.location.href = "deactivateTeam?teamId="+team_id;
		}
}

</script>			
</%def>
<%def name="head()">
<link href = "https://code.jquery.com/ui/1.10.4/themes/ui-lightness/jquery-ui.css"
         rel = "stylesheet">
</%def>

<%def name="title()">CheckMeIn Teams</%def>
<%inherit file="base.mako"/>
${self.logo()}
<A style="text-align:right" HREF="/profile/logout">Logout ${username}</A><br/>
	<fieldset>
	<legend>Add Team</legend>
    <form action="addTeam">
       <table>
	   <TD>Program Type</TD><TD><select name="programName" id="programName">
	      <option value="TFI">Non-FIRST Teams</option>
		  <option value="FLL-Discovery">FIRST Lego League Discovery</option>
		  <option value="FLL-Explore">FIRST Lego League Explore</option>
		  <option value="FLL-Challenge" selected>FIRST Lego League Challenge</option>
		  <option value="FTC">FIRST Tech Challenge (FTC)</option>
		  <option value="FRC">FIRST Robotics Challenge (FRC)</option>
		</select></td></tr>
		<TD>Program Number</TD>
		<TD><input type="number" id="programNumber" name="programNumber"></td></tr>
		<TD>Team Name</TD>
		<TD><input id="teamName" name="teamName" placeholder="To be determined"></td><tr/>
       <TD>Coach 1</TD><td><select name="coach1" id="coach1">
	   % for user in activeMembers:
	       <option value="${user[1]}">${user[0]} - ${user[1]}</option>
	   % endfor
		</select></td>
       <TD>Coach 2</TD><td><select name="coach2" id="coach2">
	   % for user in activeMembers:
	       <option value="${user[1]}">${user[0]} - ${user[1]}</option>
	   % endfor
		</select></td>		
		</tr>   
		<tr><td><input type="submit" value="Add"/></td></tr>
	</table>
	</form>
	</fieldset>
	<br/>
	<fieldset>
	    <legend>Active Teams</legend>
			<table class="teams" width="100%">
			<tr>
				<th align="left">Team ID</th>
				<th align="left">Team Name</th>
				<th align="left">Start Date</th>
				<th align="left">Coaches</th>
				
				<th align="center">Actions</th>
			</tr>
			 % for team in activeTeams:
			 <tr>
				<td><A HREF="/teams/${team.getProgramId()}">${team.getProgramId()}</A></td>
				<td><A HREF="/teams/${team.getProgramId()}">${team.name}</A></td>
				<td>${team.startDate.strftime("%d %b %Y")}</td>
				<td>
				% for coach in coaches[team.teamId]:
				    ${coach.display() + " " }
				% endfor
				</td>
				<td align="center">
					<button name="Edit">Edit Team Info</button>
					<button name="Deactivate" onclick="deactivateTeam('${team.name}', '${team.teamId}')" style="background-color: #a84232; color: #ffffff">Deactivate</button>
				</td>
			 </tr>
   			% endfor
			</table>
	</fieldset>
<hr/>
To add feature requests or report issues, please go to:<A HREF="https://github.com/alan412/CheckMeIn/issues">https://github.com/alan412/CheckMeIn/issues</A>