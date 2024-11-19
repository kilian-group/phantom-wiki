# NOTE: to generate this CFG, I used the following prompt:
# https://chatgpt.com/share/673bf38a-df2c-8011-a5fb-896067f49e5e
# but in the openai playground with the following parameters
# Model: GPT-4.0
# Temperature: 1.0
# Max Tokens: 4095
# Top-p: 1.0
# Frequency Penalty: 0.0
# Presence Penalty: 0.0

GPT_4o_OUTPUT_STRING = """
<bio> ::= <intro> <career_statement> <education_statement> <passion_statement> <accolade_statement> <project_statement> <innovation_statement> <leadership_statement> <closing_statement>

<intro> ::= <name_introduction> <origin_statement> <personal_motto>

<name_introduction> ::= "Introducing " <fixed_name> ", "

<fixed_name> ::= "Clara"

<origin_statement> ::= "a luminary from " <fictional_city> " known for her visionary tales."

<fictional_city> ::= "Zypheris" | "Eldoria" | "Loremville" | "Aetherhaven" | "Mystos" | "Arcanis" | "Novaterrae" | "Solstica"

<personal_motto> ::= "Guided by her personal mantra, \"" <motto> "\","

<motto> ::= "the future is what we create today" | "innovation fuels progress" | "exploration leads to discovery"

<career_statement> ::= "Clara's role as a " <occupation> " is defined by her " <career_trait> ", " <skill_list> ", and " <forethought> ". Her career highlights include " <career_highlight> "."

<occupation> ::= "pioneering futures trader"

<career_trait> ::= "unquenchable curiosity" | "innate strategic acumen" | "adept analytical prowess" | "forward-thinking mindset" | "fearless innovation"

<skill_list> ::= <skill> " and " <additional_skill> ", alongside " <extra_skill>

<skill> ::= "masterful negotiation skills" | "profound market insights" | "asset valuation capabilities" | "data-driven decision making"

<additional_skill> ::= "risk management" | "emerging trend analysis" | "financial forecasting" | "scenario planning"

<extra_skill> ::= "strategic scenario modeling" | "economic trend synthesis"

<forethought> ::= "preemptive market foresight" | "longitudinal thinking" | "keen-eyed forecasts" | "strategic vision" | "adaptive strategies"

<career_highlight> ::= "transforming risk assessment models" | "revolutionizing asset allocation techniques"

<education_statement> ::= <education_intro> <institution> ", where she honed her skills in " <major_subject_list> ". During her studies, she " <academic_achievement> "."

<education_intro> ::= "Clara is a distinguished graduate of "

<institution> ::= "the revered Academy of Zelphyr" | "Neoterica University" | "the prestigious Lyceum of Astra" | "the Innovatus Institute" | "Vanguard Collegium"

<major_subject_list> ::= <major_subject> " and " <additional_major_subject> ", with a focus in " <specialization>

<major_subject> ::= "quantitative analysis" | "financial modeling" | "economic theory" | "complex systems"

<additional_major_subject> ::= "behavioral finance" | "statistical algorithms" | "multi-variable investment strategies"

<specialization> ::= "advanced predictive analytics" | "synthetic fiscal frameworks" | "disruptive financial innovations"

<academic_achievement> ::= "developed pioneering quantitative models" | "published studies on predictive markets" | "created award-winning financial simulations"

<passion_statement> ::= <passion_intro> "a tireless quest for " <goal_list> " and an enduring passion for " <interest_list> ". Her latest focus has been " <focus_area> "."

<passion_intro> ::= "Her journey is fueled by "

<goal_list> ::= <goal> " alongside " <additional_goal> ", consistently striving for " <future_vision>

<goal> ::= "enhancing financial predictability" | "disrupting traditional paradigms"

<additional_goal> ::= "cultivating economic resilience" | "expanding global trade networks"

<future_vision> ::= "a seamlessly interconnected global economy" | "equality in financial opportunities"

<interest_list> ::= <interest> " as well as " <additional_interest> ", coupled with " <extra_interest>

<interest> ::= "avant-garde technologies" | "synthetic fiscal environments" | "emerging global markets" | "innovative capital solutions"

<additional_interest> ::= "dynamic risk assessment methodologies" | "virtual trading platforms"

<extra_interest> ::= "blockchain finance structures" | "cryptographic asset exchanges"

<focus_area> ::= "integrating AI in market analysis" | "eco-friendly investment strategies"

<accolade_statement> ::= <accolade_intro> <award> " and recognized for her " <notable_contribution> ". As a " <industry_role> ", she has been pivotal in " <industry_influence> "."

<accolade_intro> ::= "She has been awarded "

<award> ::= "the Altair Excellence in Trading Award" | "Lyra’s Financial Innovation Trophy" | "Mercury Master in Economics Medal"

<notable_contribution> ::= "pioneering investment algorithms" | "groundbreaking economic models" | "establishing new trading benchmarks"

<industry_role> ::= "thought leader" | "trailblazer" | "innovator"

<industry_influence> ::= "shaping regulatory frameworks" | "advancing fintech collaborations" | "promoting ethical trading practices"

<project_statement> ::= <project_intro> <project> " that aims to redefine " <new_initiative> ". She also developed " <secondary_project> " and is currently spearheading " <ongoing_project> "."

<project_intro> ::= "Clara recently launched "

<project> ::= "the Quantum Synergy Initiative" | "Project Luminos" | "Integra Visionary Platform"

<new_initiative> ::= "market prediction dynamics" | "investment risk paradigms" | "future trading ecosystems"

<secondary_project> ::= "the Helios Trading Interface" | "Carta Nexus" | "the Equilibrium Analytics Suite"

<ongoing_project> ::= "the Aurora Exchange Expansion" | "Project Quantum Equities"

<innovation_statement> ::= "With her innovative approach, Clara has developed " <invention> " which " <innovation_impact> "."

<invention> ::= "a multi-layered predictive analytics engine" | "a sustainable investment pathfinder"

<innovation_impact> ::= "enhances data coherence" | "optimizes resource allocation" | "integrates real-time market variables"

<leadership_statement> ::= "As the founder of " <organization> ", she " <leadership_action> ", transforming " <sector_impact> "."

<organization> ::= "the Global Futures Coalition" | "Innovate Finance Network" | "Synergia Developments"

<leadership_action> ::= "leads transformative industry dialogues" | "mentors emerging market analysts"

<sector_impact> ::= "the landscape of international trading" | "financial governance protocols"

<closing_statement> ::= "Clara continues to reshape the world of " <field_of_influence> ", one bold prediction at a time."

<field_of_influence> ::= "financial speculations" | "market dynamics" | "trading futures" | "global economic landscapes" | "cutting-edge financial technologies"
"""

from phantom_wiki.utils.parsing import (one_line_cfg, 
                                        remove_brackets, 
                                        substitute_arrow)
def formatting_raw_input(raw_text):
    # delete the ``` and strip the text
    processed_text = raw_text.replace("```", "").strip()
    # sustitue '<>' with '' using regex
    processed_text = remove_brackets(processed_text)
    # substitute '::=' with '->'
    processed_text = substitute_arrow(processed_text)
    # convert to one line CFG
    processed_text = one_line_cfg(processed_text)

    return processed_text
formatted_cfg_string = formatting_raw_input(GPT_4o_OUTPUT_STRING)
print(formatted_cfg_string)
"""
bio -> intro career_statement education_statement passion_statement accolade_statement project_statement innovation_statement leadership_statement closing_statement 
intro -> name_introduction origin_statement personal_motto 
name_introduction -> "Introducing " fixed_name ", " 
fixed_name -> "Clara" 
origin_statement -> "a luminary from " fictional_city " known for her visionary tales." 
fictional_city -> "Zypheris" | "Eldoria" | "Loremville" | "Aetherhaven" | "Mystos" | "Arcanis" | "Novaterrae" | "Solstica" 
personal_motto -> "Guided by her personal mantra, "" motto ""," 
motto -> "the future is what we create today" | "innovation fuels progress" | "exploration leads to discovery" 
career_statement -> "Clara's role as a " occupation " is defined by her " career_trait ", " skill_list ", and " forethought ". Her career highlights include " career_highlight "." 
occupation -> "pioneering futures trader" 
career_trait -> "unquenchable curiosity" | "innate strategic acumen" | "adept analytical prowess" | "forward-thinking mindset" | "fearless innovation" 
skill_list -> skill " and " additional_skill ", alongside " extra_skill 
skill -> "masterful negotiation skills" | "profound market insights" | "asset valuation capabilities" | "data-driven decision making" 
additional_skill -> "risk management" | "emerging trend analysis" | "financial forecasting" | "scenario planning" 
extra_skill -> "strategic scenario modeling" | "economic trend synthesis" 
forethought -> "preemptive market foresight" | "longitudinal thinking" | "keen-eyed forecasts" | "strategic vision" | "adaptive strategies" 
career_highlight -> "transforming risk assessment models" | "revolutionizing asset allocation techniques" 
education_statement -> education_intro institution ", where she honed her skills in " major_subject_list ". During her studies, she " academic_achievement "." 
education_intro -> "Clara is a distinguished graduate of " 
institution -> "the revered Academy of Zelphyr" | "Neoterica University" | "the prestigious Lyceum of Astra" | "the Innovatus Institute" | "Vanguard Collegium" 
major_subject_list -> major_subject " and " additional_major_subject ", with a focus in " specialization 
major_subject -> "quantitative analysis" | "financial modeling" | "economic theory" | "complex systems" 
additional_major_subject -> "behavioral finance" | "statistical algorithms" | "multi-variable investment strategies" 
specialization -> "advanced predictive analytics" | "synthetic fiscal frameworks" | "disruptive financial innovations" 
academic_achievement -> "developed pioneering quantitative models" | "published studies on predictive markets" | "created award-winning financial simulations" 
passion_statement -> passion_intro "a tireless quest for " goal_list " and an enduring passion for " interest_list ". Her latest focus has been " focus_area "." 
passion_intro -> "Her journey is fueled by " 
goal_list -> goal " alongside " additional_goal ", consistently striving for " future_vision 
goal -> "enhancing financial predictability" | "disrupting traditional paradigms" 
additional_goal -> "cultivating economic resilience" | "expanding global trade networks" 
future_vision -> "a seamlessly interconnected global economy" | "equality in financial opportunities" 
interest_list -> interest " as well as " additional_interest ", coupled with " extra_interest 
interest -> "avant-garde technologies" | "synthetic fiscal environments" | "emerging global markets" | "innovative capital solutions" 
additional_interest -> "dynamic risk assessment methodologies" | "virtual trading platforms" 
extra_interest -> "blockchain finance structures" | "cryptographic asset exchanges" 
focus_area -> "integrating AI in market analysis" | "eco-friendly investment strategies" 
accolade_statement -> accolade_intro award " and recognized for her " notable_contribution ". As a " industry_role ", she has been pivotal in " industry_influence "." 
accolade_intro -> "She has been awarded " 
award -> "the Altair Excellence in Trading Award" | "Lyra’s Financial Innovation Trophy" | "Mercury Master in Economics Medal" 
notable_contribution -> "pioneering investment algorithms" | "groundbreaking economic models" | "establishing new trading benchmarks" 
industry_role -> "thought leader" | "trailblazer" | "innovator" 
industry_influence -> "shaping regulatory frameworks" | "advancing fintech collaborations" | "promoting ethical trading practices" 
project_statement -> project_intro project " that aims to redefine " new_initiative ". She also developed " secondary_project " and is currently spearheading " ongoing_project "." 
project_intro -> "Clara recently launched " 
project -> "the Quantum Synergy Initiative" | "Project Luminos" | "Integra Visionary Platform" 
new_initiative -> "market prediction dynamics" | "investment risk paradigms" | "future trading ecosystems" 
secondary_project -> "the Helios Trading Interface" | "Carta Nexus" | "the Equilibrium Analytics Suite" 
ongoing_project -> "the Aurora Exchange Expansion" | "Project Quantum Equities" 
innovation_statement -> "With her innovative approach, Clara has developed " invention " which " innovation_impact "." 
invention -> "a multi-layered predictive analytics engine" | "a sustainable investment pathfinder" 
innovation_impact -> "enhances data coherence" | "optimizes resource allocation" | "integrates real-time market variables" 
leadership_statement -> "As the founder of " organization ", she " leadership_action ", transforming " sector_impact "." 
organization -> "the Global Futures Coalition" | "Innovate Finance Network" | "Synergia Developments" 
leadership_action -> "leads transformative industry dialogues" | "mentors emerging market analysts" 
sector_impact -> "the landscape of international trading" | "financial governance protocols" 
closing_statement -> "Clara continues to reshape the world of " field_of_influence ", one bold prediction at a time." 
field_of_influence -> "financial speculations" | "market dynamics" | "trading futures" | "global economic landscapes" | "cutting-edge financial technologies"
"""

print("================================")

from nltk import CFG
cfg = CFG.fromstring(formatted_cfg_string)

print(cfg)

print("================================")

from nltk.parse.generate import generate
import os
import textwrap
os.makedirs("out", exist_ok=True)
sentences = list(generate(cfg, n=1000000))
# randomly sample 5 sentences
import random
random.seed(1)
sentences = random.sample(sentences, 5)
for i, sentence in enumerate(sentences):
    with open(f"out/generation_{i+1}.txt", "w") as file:
        file.write(textwrap.fill(' '.join(sentence) + "\n"))
    