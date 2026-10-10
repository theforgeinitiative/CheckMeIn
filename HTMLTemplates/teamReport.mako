<%def name="scripts()">
</%def>
<%def name="head()">
</%def>

<%def name="title()">CheckMeIn Team Report</%def>
<%inherit file="base.mako"/>
<CENTER>
${self.logo()}<br/>
</CENTER>
<H1> Team List </H1>
<UL>
% for team in teams:
   <LI>${team.getProgramId()} - ${team.name}
   <UL>
      <LI><B>Checked in: ${team.totalPresent}</B>
          (Student: ${team.counts[TeamMemberType.student]},
           Coach: ${team.counts[TeamMemberType.coach]},
           Mentor: ${team.counts[TeamMemberType.mentor]},
           Other: ${team.counts[TeamMemberType.other]})
      </LI>
   % for member in team.members:
     <LI>${member.name} ${member.typeString()}</LI>
   % endfor %
   </UL></LI>
% endfor 
</UL>