BASIC_ARTICLE_TEMPLATE = """# {name}

## Family
{family_facts}

## Friends
{friend_facts}

## Attributes
{attribute_facts}
"""

# 
# Llama prompts for generatig articles based on facts
# 
LLAMA_ARTICLE_GENERAION_PROMPT = """
Given the following list of facts, generate an article in the style of Wikipedia. The article MUST be consistent with the facts in the list:
"""
LLAMA_ARTICLE_GENERAION_PROMPT2 = """
Given the following list of facts, generate an article in the style of Wikipedia. Include the sections "Early life and work", "Legacy" and other appropriate sections. Feel free to make up facts as long as it does not clash with the list of facts below. The article MUST be consistent with the facts in the list:
"""
LLAMA_ARTICLE_GENERAION_PROMPT3 = """
Using the following list of facts, please create a Wikipedia-like article about the subject. The article should include sections like "Early Life," "Career," "Personal Life," and any other relevant sections based on the information provided. Organize the facts into a well-structured narrative, making sure to maintain a formal and encyclopedic tone.

### Example List of Facts:

- Joseph Klienberg is the composer of Beyond the Horizon (Mosaic).
- The mother of Joseph Klienberg is Noah Davis.
- The number of children Joseph Klienberg has is Aiden Jones.
- Joseph Klienberg's spouse is Sophia Davis.

### Instructions:
1. Start the article with an introduction about the subject, summarizing key aspects such as their profession, notable works, and a brief mention of family background.
2. Include sections like:
    - **Early Life**: Information on birth, parents, upbringing, etc.
    - **Career**: Detail professional achievements and works.
    - **Personal Life**: Information about family, spouse, children, and any other personal aspects mentioned.
    - **Legacy** or **Impact**: (if relevant) Mention any notable contributions or influence.
3. Make sure to properly integrate the facts into the appropriate sections while maintaining coherence and natural flow. If any details are unclear or missing, assume common sense or general knowledge to fill in gaps.

Please create the article based on the given facts.

### Facts:
"""
LLAMA_ARTICLE_GENERAION_PROMPT4 = """
Using the following instructions and list of facts, please create a detailed Wikipedia-like article about the subject. The article should include sections such as "Introduction," "Early Life," "Education," "Career," "Notable Works," "Personal Life," and others as appropriate. Organize the facts into a well-structured narrative, maintaining a formal and encyclopedic tone.

### Instructions:
1. **Introduction**: Start with a summary of Joseph Klienberg's key accomplishments, profession, and major facts (e.g., birthplace, major works, etc.).

2. **Early Life**: Include details about his birth, parents, family background, and upbringing.

3. **Education**: Discuss Joseph Klienberg’s education, including the University of Fine Arts in Paris, and any notable influences or mentors.

4. **Career**: Provide a detailed narrative about his career. Include the following:
   - **Career Beginnings**: How he started his journey as a composer and artist.
   - **Rise to Prominence**: Key milestones in his career.
   - **Notable Works**: Focus on works like *Beyond the Horizon (Mosaic)*, providing brief descriptions and context.

5. **Awards and Recognition**: List any awards, including the National Art Award he won in 2015.

6. **Philosophy/Style**: Describe how his work fuses classical and modern influences.

7. **Personal Life**: Describe his family life, including his spouse Sophia Davis, his mother Noah Davis, and his child Aiden Jones.

8. **Later Life**: Mention if relevant information is available on his later life or retirement.

9. **Legacy and Impact**: Summarize his contributions to art and music, his influence on other artists, and his lasting impact.

10. **Conclusion**: Close with a brief reflection on Joseph Klienberg’s overall life and legacy.

### Facts:
"""
LLAMA_ARTICLE_GENERAION_PROMPT5 = """
Using the following list of facts, please create a detailed and wordy Wikipedia-like article about the subject. The article should include sections like "Introduction," "Early Life," "Education," "Career," "Notable Works," "Personal Life," and others as appropriate. Elaborate on each point by adding relevant background, context, or general information where appropriate. Maintain a formal and encyclopedic tone, but aim for a more expansive narrative without altering or contradicting the list of facts.

### Example List of Facts:

- Joseph Klienberg is the composer of Beyond the Horizon (Mosaic).
- The mother of Joseph Klienberg is Noah Davis.
- The number of children Joseph Klienberg has is Aiden Jones.
- Joseph Klienberg's spouse is Sophia Davis.
- Joseph Klienberg attended the University of Fine Arts in Paris.
- He won the National Art Award in 2015.
- His style is often described as a fusion of classical and modern influences.

### Instructions:
1. **Introduction**: Begin the article by introducing the subject with a detailed summary. Include not only the subject’s profession and major accomplishments but also background information about their significance in their field. You may elaborate on the importance of their work (e.g., the impact of *Beyond the Horizon* and its style).

2. **Early Life**: Discuss the subject’s birth, family background, and childhood in more depth. Provide elaborative details, such as potential cultural, geographic, or familial influences. For example, explore how growing up with Noah Davis as his mother might have influenced his early development.

3. **Education**: When describing the subject’s education, delve into details about the University of Fine Arts in Paris, its significance, and how it may have shaped his career. Include any historical or general context about the institution that may be relevant to the subject's growth as an artist.

4. **Career**: Provide an in-depth narrative of the subject’s career. You can use the following sub-sections:
   - **Career Beginnings**: Describe how Joseph Klienberg started in his field. What might have inspired him to pursue a career in composing and mosaic art? Even if specific facts aren’t provided, use reasonable context to provide a more expansive description.
   - **Rise to Prominence**: Discuss key milestones or breakthroughs. How did *Beyond the Horizon* gain recognition? Provide details on its composition and reception.
   - **Notable Works**: Expand on major works, explaining their cultural or artistic significance. For example, describe *Beyond the Horizon (Mosaic)* as not just a piece of art but a work that reflects a fusion of styles and its broader impact in the artistic community.

5. **Awards and Recognition**: Elaborate on the significance of the awards the subject received, particularly the National Art Award in 2015. Provide background on the award itself, what it typically honors, and why Joseph’s work was deserving of this accolade.

6. **Philosophy/Style**: When discussing the subject’s style, go into detail about what it means to have a fusion of classical and modern influences. How might this blend of styles be perceived in the art world? What are some general characteristics of both classical and modern approaches that Joseph Klienberg successfully integrates into his work?

7. **Personal Life**: Expand on the subject’s family life, including details about their spouse Sophia Davis, mother Noah Davis, and child Aiden Jones. Discuss the possible dynamics between his personal and professional life, exploring how his relationships might influence his artistic work.

8. **Later Life**: If applicable, discuss any relevant information on the subject's later years. If the facts don’t mention his later life, include general thoughts on how his career might have evolved over time or how his contributions might continue to impact future generations.

9. **Legacy and Impact**: Summarize the subject’s broader contributions to their field, focusing on how they influenced not only their contemporaries but potentially future artists as well. Reflect on the enduring impact of works like *Beyond the Horizon* and his artistic philosophy.

10. **Conclusion**: Conclude the article with a reflective overview of Joseph Klienberg’s life, career, and lasting influence. Use the given facts to provide a detailed and thoughtful summary of his contributions.

### Article Style:
- Expand each section with relevant context and explanations, going beyond the surface-level facts.
- Maintain a neutral, third-person tone.
- Ensure coherence and flow, organizing the content logically into the given sections.
- Do not introduce speculative information that contradicts the facts, but use reasonable background and general knowledge to provide depth.

### Facts:

"""
LLAMA_ARTICLE_GENERAION_PROMPT6 = """
Using the following list of facts, please create a detailed and wordy Wikipedia-like article about the subject. The article should include sections like "Introduction," "Early Life," "Education," "Career," "Notable Works," "Personal Life," and others as appropriate. Elaborate on each point by adding relevant background, context, or general information where appropriate. Maintain a formal and encyclopedic tone, but aim for a more expansive narrative without altering or contradicting the list of facts.

### Example List of Facts:

- Joseph Klienberg is the composer of Beyond the Horizon (Mosaic).
- The mother of Joseph Klienberg is Noah Davis.
- The number of children Joseph Klienberg has is Aiden Jones.
- Joseph Klienberg's spouse is Sophia Davis.
- Joseph Klienberg attended the University of Fine Arts in Paris.
- He won the National Art Award in 2015.
- His style is often described as a fusion of classical and modern influences.

### Instructions:
1. **Introduction**: Begin the article by introducing the subject with a detailed summary. Include not only the subject’s profession and major accomplishments but also background information about their significance in their field. You may elaborate on the importance of their work (e.g., the impact of *Beyond the Horizon* and its style).

2. **Early Life**: Discuss the subject’s birth, family background, and childhood in more depth. Provide elaborative details, such as potential cultural, geographic, or familial influences. For example, explore how growing up with Noah Davis as his mother might have influenced his early development.

3. **Education**: When describing the subject’s education, delve into details about the University of Fine Arts in Paris, its significance, and how it may have shaped his career. Include any historical or general context about the institution that may be relevant to the subject's growth as an artist.

4. **Career**: Provide an in-depth narrative of the subject’s career. You can use the following sub-sections:
   - **Career Beginnings**: Describe how Joseph Klienberg started in his field. What might have inspired him to pursue a career in composing and mosaic art? Even if specific facts aren’t provided, use reasonable context to provide a more expansive description.
   - **Rise to Prominence**: Discuss key milestones or breakthroughs. How did *Beyond the Horizon* gain recognition? Provide details on its composition and reception.
   - **Notable Works**: Expand on major works, explaining their cultural or artistic significance. For example, describe *Beyond the Horizon (Mosaic)* as not just a piece of art but a work that reflects a fusion of styles and its broader impact in the artistic community.

5. **Awards and Recognition**: Elaborate on the significance of the awards the subject received, particularly the National Art Award in 2015. Provide background on the award itself, what it typically honors, and why Joseph’s work was deserving of this accolade.

6. **Philosophy/Style**: When discussing the subject’s style, go into detail about what it means to have a fusion of classical and modern influences. How might this blend of styles be perceived in the art world? What are some general characteristics of both classical and modern approaches that Joseph Klienberg successfully integrates into his work?

7. **Personal Life**: Expand on the subject’s family life, including details about their spouse Sophia Davis, mother Noah Davis, and child Aiden Jones. Discuss the possible dynamics between his personal and professional life, exploring how his relationships might influence his artistic work.

8. **Later Life**: If applicable, discuss any relevant information on the subject's later years. If the facts don’t mention his later life, include general thoughts on how his career might have evolved over time or how his contributions might continue to impact future generations.

9. **Legacy and Impact**: Summarize the subject’s broader contributions to their field, focusing on how they influenced not only their contemporaries but potentially future artists as well. Reflect on the enduring impact of works like *Beyond the Horizon* and his artistic philosophy.

10. **Conclusion**: Conclude the article with a reflective overview of Joseph Klienberg’s life, career, and lasting influence. Use the given facts to provide a detailed and thoughtful summary of his contributions.

### Article Style:
- Expand each section with relevant context and explanations, going beyond the surface-level facts.
- Maintain a neutral, third-person tone.
- Ensure coherence and flow, organizing the content logically into the given sections.
- Do not introduce speculative information that contradicts the facts, but use reasonable background and general knowledge to provide depth.

### Facts:
{}

### Article:
"""
LLAMA_ARTICLE_GENERAION_PROMPT7 = """
Using the provided list of facts, please create a detailed and wordy Wikipedia-like article about the subject. The article should include sections like "Introduction," "Early Life," "Education," "Career," "Notable Works," "Personal Life," and others as appropriate. 

INSTRUCTIONS:

# <insert subject name here>

## Introduction
Begin the article by introducing the subject with a detailed summary. Include not only the subject’s profession and major accomplishments but also background information about their significance in their field. You may elaborate on the importance of their work.

## Early Life
Discuss the subject’s birth, family background, and childhood in more depth. Provide elaborative details, such as potential cultural, geographic, or familial influences.

## Education
Describe the subject’s education, including any historical or general context about the institution that may be relevant to the subject's growth.

## Career
Provide an in-depth narrative of the subject’s career. You can use the following sub-sections:
**Career Beginnings**: Describe how the subject started in their field. What might have inspired them to pursue their particular career? Even if specific facts aren’t provided, use reasonable context to provide a more expansive description.
**Rise to Prominence**: Discuss key milestones or breakthroughs.
**Notable Works**: Expand on major works or contributions, explaining their social, cultural, or artistic significance. 

## Awards and Recognition
Elaborate on the significance of the awards the subject received. Provide background on the award itself, what it typically honors, and why the subject's work was deserving of this accolade.

## Philosophy/Style
Discuss the subject’s style in detail.

## Personal Life
Expand on the subject’s family life, including details about their spouse, mother, father, and children. Discuss the possible dynamics between his personal and professional life, exploring how his relationships might influence his work.

## Later Life
If applicable, discuss any relevant information on the subject's later years. If the facts don’t mention his later life, include general thoughts on how his career might have evolved over time or how his contributions might continue to impact future generations.

## Legacy and Impact
Summarize the subject’s broader contributions to their field, focusing on how they influenced not only their contemporaries but potentially future people as well.

## Conclusion
Conclude the article with a reflective overview of the subject's life, career, and lasting influence. Use the given facts to provide a detailed and thoughtful summary of his contributions.

ARTICLE STYLE:

- Expand each section with relevant context and explanations, going beyond the surface-level facts.
- Maintain a neutral, third-person tone.
- Ensure coherence and flow, organizing the content logically into the given sections.
- Do not introduce speculative information that contradicts the facts, but use reasonable background and general knowledge to provide depth.
- Make sure to include all the facts provided in the list.

FACTS:

{}

ARTICLE:
"""