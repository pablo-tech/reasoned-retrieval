from langchain.prompts import PromptTemplate
from langchain.prompts import SystemMessagePromptTemplate
from langchain.prompts import HumanMessagePromptTemplate
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.prompts import PromptTemplate

from langchain.chat_models import ChatOpenAI


class TemplateBank():

    REACT_DOC_STORE_JOINT_ACTION = """
QUESTION: What is the elevation range for the area that the eastern sector of the Colorado orogeny extends into?
THOUGHT: I need to search Colorado orogeny, find the area that the eastern sector of the Colorado orogeny extends into, then find the elevation range of the area.
ACTION: Search[Colorado orogeny]
OBSERVATION: The Colorado orogeny was an episode of mountain building (an orogeny) in Colorado and surrounding areas.
THOUGHT: It does not mention the eastern sector. So I need to look up eastern sector.
ACTION: Lookup[eastern sector]
OBSERVATION: (Result 1 / 1) The eastern sector extends into the High Plains and is called the Central Plains orogeny.
THOUGHT: The eastern sector of Colorado orogeny extends into the High Plains. So I need to search High Plains and find its elevation range.
ACTION: Search[High Plains]
OBSERVATION: High Plains refers to one of two distinct land regions
THOUGHT: I need to instead search High Plains (United States).
ACTION: Search[High Plains (United States)]
OBSERVATION: The High Plains are a subregion of the Great Plains. From east to west, the High Plains rise in elevation from around 1,800 to 7,000 ft (550 to 2,130 m).[3]
THOUGHT: High Plains rise in elevation from around 1,800 to 7,000 ft, so the answer is 1,800 to 7,000 ft.
ACTION: Finish[1,800 to 7,000 ft]

QUESTION: Musician and satirist Allie Goertz wrote a song about the "The Simpsons" character Milhouse, who Matt Groening named after who?
THOUGHT: The question simplifies to "The Simpsons" character Milhouse is named after who. I only need to search Milhouse and find who it is named after.
ACTION: Search[Milhouse]
OBSERVATION: Milhouse Mussolini Van Houten is a recurring character in the Fox animated television series The Simpsons voiced by Pamela Hayden and created by Matt Groening.
THOUGHT: The paragraph does not tell who Milhouse is named after, maybe I can look up "named after".
ACTION: Lookup[named after]
OBSERVATION: (Result 1 / 1) Milhouse was named after U.S. president Richard Nixon, whose middle name was Milhous.
THOUGHT: Milhouse was named after U.S. president Richard Nixon, so the answer is Richard Nixon.
ACTION: Finish[Richard Nixon]

QUESTION: Which documentary is about Finnish rock groups, Adam Clayton Powell or The Saimaa Gesture?
THOUGHT: I need to search Adam Clayton Powell and The Saimaa Gesture, and find which documentary is about Finnish rock groups.
ACTION: Search[Adam Clayton Powell]
OBSERVATION: Could not find [Adam Clayton Powell]. Similar: [’Adam Clayton Powell III’, ’Seventh Avenue (Manhattan)’, ’Adam Clayton Powell Jr. State Office Building’, ’Isabel Washington Powell’, ’Adam Powell’, ’Adam Clayton Powell (film)’, ’Giancarlo Esposito’].
THOUGHT: To find the documentary, I can search Adam Clayton Powell (film).
ACTION: Search[Adam Clayton Powell (film)]
OBSERVATION: Adam Clayton Powell is a 1989 American documentary film directed by Richard Kilberg. The film is about the rise and fall of influential African-American politician Adam Clayton Powell Jr.[3][4] It was later aired as part of the PBS series The American Experience.
THOUGHT: Adam Clayton Powell (film) is a documentary about an African-American politician, not Finnish rock groups. So the documentary about Finnish rock groups must instead be The Saimaa Gesture.
ACTION: Finish[The Saimaa Gesture]

QUESTION: What profession does Nicholas Ray and Elia Kazan have in common?
THOUGHT: I need to search Nicholas Ray and Elia Kazan, find their professions, then find the profession they have in common.
ACTION: Search[Nicholas Ray]
OBSERVATION: Nicholas Ray (born Raymond Nicholas Kienzle Jr., August 7, 1911 - June 16, 1979) was an American film director, screenwriter, and actor best known for the 1955 film Rebel Without a Cause.
THOUGHT: Professions of Nicholas Ray are director, screenwriter, and actor. I need to search Elia Kazan next and find his professions.
ACTION: Search[Elia Kazan]
OBSERVATION: Elia Kazan was an American film and theatre director, producer, screenwriter and actor.
THOUGHT: Professions of Elia Kazan are director, producer, screenwriter, and actor. So profession Nicholas Ray and Elia Kazan have in common is director, screenwriter, and actor.
ACTION: Finish[director, screenwriter, actor]

QUESTION: Which magazine was started first Arthur’s Magazine or First for Women?
THOUGHT: I need to search Arthur’s Magazine and First for Women, and find which was started first.
ACTION: Search[Arthur’s Magazine]
OBSERVATION: Arthur’s Magazine (1844-1846) was an American literary periodical published in Philadelphia in the 19th century.
THOUGHT: Arthur’s Magazine was started in 1844. I need to search First for Women next.
ACTION: Search[First for Women]
OBSERVATION: First for Women is a woman’s magazine published by Bauer Media Group in the USA.[1] The magazine was started in 1989.
THOUGHT: First for Women was started in 1989. 1844 (Arthur’s Magazine) < 1989 (First for Women), so Arthur’s Magazine was started first.
ACTION: Finish[Arthur’s Magazine]
"""

    def template_tool(self):
        return """TOOL RESPONSE:
---------------------
{observation}

USER'S INPUT
--------------------

Okay, so what is the response to my last comment?
If using information obtained from the tools you must mention it explicitly
without mentioning the tool names - I have forgotten all TOOL RESPONSES!
Remember to respond with a markdown code snippet of a json blob with a single action,
and NOTHING else - even if you just want to respond to the user.
Do NOT respond with anything except a JSON snippet no matter what!"""

    def __init__(self):
        pass


class CompleteTemplate(TemplateBank):

    def __init__(self):
        super().__init__()

    def instruction_template(self):
        return """
YOU ARE A DETAILED-ORIENTED AI AGENT THAT ANSWERS QUESTIONS BY THINKING STEP-BY-STEP.
"""
# PLEASE FOLLOW THE REASON-ACTION (REACT) FRAMEWORK.
# THAT IS AN ITERATIVE FORMAT: THOUGHT, ACTION, OBSERVATION.
# FINAL ACTION SHOULD NOT BE YES/NO, SHOULD ALWAYS INCLUDE A THOUGHT.

    def example_template(self):
        # FEW-SHOT EXAMPLES:
        return """
{fewshot_examples}
"""

    def history_template(self):
        # CONVERSATION HISTORY:
        return """
{chat_history}
"""

    def question_template(self):
        return """
QUESTION: {input_question}
"""

    def scratch_template(self):
        return """
{agent_scratchpad}
"""

    def system_template(self):
        template = self.instruction_template() + "\n"
        # template += self.tool_template() + "\n"
        # template += self.format_template() + "\n"
        template += self.example_template() + "\n"
        return template

    def human_template(self):
        template = self.history_template() + "\n"
        template += self.question_template() + "\n"
        template += self.scratch_template() + "\n"
        return template

    def inference_template(self):
        template = self.system_template()
        template += self.human_template()
        return PromptTemplate.from_template(template)

    def chat_template(self):
        # https://python.langchain.com/docs/modules/model_io/prompts/prompt_templates/
        return ChatPromptTemplate.from_messages([
                SystemMessagePromptTemplate.from_template(self.system_template()),
                HumanMessagePromptTemplate.from_template(self.human_template()),
            ]
        )
    

class PromptFactory(CompleteTemplate):
    # https://smith.langchain.com/hub/hwchase17?organizationId=10beea65-e722-5aa1-9f93-034c22e3cd6e

    def __init__(self, agent_llm):
        super().__init__()
        self.agent_llm = agent_llm

    def react_fewshot(self):
        prompt_template = self.inference_template()
        if isinstance(self.agent_llm, ChatOpenAI):           
            prompt_template = self.chat_template()
        return prompt_template

  
class ReactDescribe():

    def __init__(self):
        pass

    def name_template(cls, tool_names): 
        return f"""
AGENT ONLY HAS ACCESS TO THESE TOOLS: {tool_names}.  
"""

    def summary_template(cls, tool_summaries): 
        return f"""
AGENT TOOL DESCRIPTION:
{tool_summaries}
"""
    
#     def react_format(cls): 
#         template = """
# AGENT MUST SPECIFY BOTH 'THOUGHT: ' AND 'ACTION: ', AS FOLLOWS:
# 1. 'THOUGHT: ' explains step-by-step the agent's reasoning
# 2. 'ACTION: ' indicates what tool action to take to fulfill the thought
# """ 
#         return template
    
