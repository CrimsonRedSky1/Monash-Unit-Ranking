"""University identities and official catalogue links shared by the website/API."""
UNIVERSITIES = [
 {'id':'monash','locations':[{'country':'Australia','city':'Melbourne'}],'aliases':['Monash'],'name':'Monash University','short_name':'Monash','location':'Melbourne, Victoria','handbook':'https://handbook.monash.edu/2026'},
 {'id':'unimelb','locations':[{'country':'Australia','city':'Melbourne'}],'aliases':['UniMelb','Melbourne University'],'name':'University of Melbourne','short_name':'Melbourne','location':'Melbourne, Victoria','handbook':'https://handbook.unimelb.edu.au/2026'},
 {'id':'rmit','locations':[{'country':'Australia','city':'Melbourne'}],'aliases':['Royal Melbourne Institute of Technology'],'name':'RMIT University','short_name':'RMIT','location':'Melbourne, Victoria','handbook':'https://handbook.rmit.edu.au/ords/r/rmit/catalogue/home'},
 {'id':'deakin','locations':[{'country':'Australia','city':c} for c in ['Melbourne','Geelong','Warrnambool']],'aliases':['Deakin'],'name':'Deakin University','short_name':'Deakin','location':'Victoria, Australia','handbook':'https://handbook.deakin.edu.au/current-students-courses/unit-search.php?year=2026'},
]
# Official code convention: https://www.deakin.edu.au/students/enrolment-and-fees/enrol/enrolment-codes-and-terminology
DEAKIN_FACULTIES={'A':'Arts and Education','E':'Arts and Education','H':'Health','M':'Business and Law','S':'Science, Engineering and Built Environment'}
