from langchain_core.messages import HumanMessage, AIMessage
 
 #Create a memory class to store the conversation history
def build_memory_from_db(messages):
     history = []
     for message in messages:
         if message.role == 'user':
             history.append(HumanMessage(content=message.message))
         else:
             history.append(AIMessage(content=message.message))
     return history