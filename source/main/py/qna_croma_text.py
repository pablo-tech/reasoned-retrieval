# from qna_example import TagConfig


# class CromaText():
    
#     def remove_punctuation(text,
#                            to_remove = ["(", ")", ":", ",", "|", "!", "?", "+", "/"]):
#         try:        
#             # print.write("punctuation_in=" + str(text))        
#             text = text.strip() 
#             for removable in to_remove:
#                 text = text.replace(removable, "")
#             # print.write("punctuation_out=" + str(text))
#             return text
#         except Exception as e:
#             print.write(text + str(e))
#             return ""

#     def post_split_remove(words,
#                           to_remove = [".", "+"]):
#         clean = []
#         for word in words:
#             for removable in to_remove:
#                 last = len(word)-1
#                 if word[last] == removable: 
#                     word = word[:last]
#             word = word.strip()
#             if word != "":
#                 clean.append(word)
#         return clean
    
    # def tag_config(tag_processor):
    #     croma_config = TagConfig(is_source_primary=False,
    #                 is_example_title_primary=True, is_example_subtitle_primary=False, is_example_text_primary=False,
    #                 is_section_heading_primary=True, is_element_text_primary=False,
    #                 is_source_secondary=True,
    #                 primary_tagging_func=tag_processor.tag_words,
    #                 is_example_title_secondary=False, is_example_subtitle_secondary=True, is_example_text_secondary=True,
    #                 is_section_heading_secondary=False, is_element_text_secondary=True,
    #                 secondary_tagging_func=tag_processor.tag_words)
    #     return croma_config
