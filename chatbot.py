import re
import pandas as pd
import openai
import os
from typing import Dict, Any
import numpy as np
from datetime import datetime
from dotenv import load_dotenv

class FinancialChatbot:
    def __init__(self):
        # Initialize OpenAI API (replace with your actual API key securely from environment variables)
        openai.api_key = os.getenv('OPENAI_API_KEY')
        
        # Initialize fields dictionary
        self.fields = {
            'loan_amount': None,
            'promotion_applied': None,
            'loan_purpose': None,
            'how_heard': None,
            'first_name': None,
            'last_name': None,
            'membership_status': None,
            'account_number': None,
            'telephone': None,
            'email': None,
            'date_of_birth': None,
            'marital_status': None,
            'whatsapp_opt_in': None,
            'employer_name': None,
            'self_employed': None,
            'primary_income': None,
            'additional_income': None,
            'total_income': None,
            'commitments': [],
            'declaration': None,
            'uploaded_ids': [],
            'uploaded_documents': [],
            'reference1_name': None,
            'reference1_relation': None,
            'reference1_address': None,
            'reference1_contact': None,
            'reference1_occupation': None,
            'reference2_name': None,
            'reference2_relation': None,
            'reference2_address': None,
            'reference2_contact': None,
            'reference2_occupation': None
        }
        
        # Conversation flow
        self.conversation_order = [
            'first_name', 'last_name', 'telephone', 'email', 'date_of_birth', 
            'loan_amount', 'loan_purpose', 'membership_status', 
            'marital_status', 'employer_name', 'self_employed', 
            'primary_income', 'additional_income', 
            'reference1_name', 'reference1_relation', 'reference1_contact',
            'reference2_name', 'reference2_relation', 'reference2_contact',
            'declaration', 'whatsapp_opt_in'
        ]
        
        # Current conversation index
        self.current_index = 0
    
    def extract_details(self, field: str, user_input: str) -> Any:
        """
        Intelligent detail extraction using OpenAI's model
        """
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": f"Extract {field} from the following text. Return only the extracted value or None."},
                    {"role": "user", "content": user_input}
                ]
            )
            extracted_value = response.choices[0].message['content'].strip()
            return extracted_value if extracted_value.lower() != 'none' else None
        except Exception as e:
            print(f"OpenAI API error: {e}")
            return None
    
    def get_next_missing_field(self):
        """
        Find the next field that hasn't been filled
        """
        for field in self.conversation_order[self.current_index:]:
            if self.fields[field] is None:
                return field
        return None
    
    def generate_question(self, field: str) -> str:
        """
        Generate conversational questions for each field
        """
        questions = {
            'first_name': "Could you please tell me your first name?",
            'last_name': "What is your last name?",
            'telephone': "What is the best contact number to reach you?",
            'email': "What is your email address?",
            'date_of_birth': "When were you born? (Please provide in DD/MM/YYYY format)",
            'loan_amount': "What loan amount are you looking for and its purpose?",
            'loan_purpose': "Could you elaborate on the purpose of your loan?",
            'membership_status': "Are you currently a member of our program?",
            'marital_status': "What is your marital status?",
            'employer_name': "Who is your current employer?",
            'self_employed': "Are you self-employed?",
            'primary_income': "What is your primary monthly income?",
            'additional_income': "Do you have any additional sources of income?",
            'reference1_name': "Could you provide the name of your first reference?",
            'reference1_relation': "What is your relationship with this reference?",
            'reference1_contact': "What is the contact number for your first reference?",
            'reference2_name': "Could you provide the name of your second reference?",
            'reference2_relation': "What is your relationship with this second reference?",
            'reference2_contact': "What is the contact number for your second reference?",
            'declaration': "Do you agree to our terms and conditions?",
            'whatsapp_opt_in': "Would you like to opt-in for WhatsApp notifications?"
        }
        return questions.get(field, f"Please provide information about {field}")
    
    def process_user_input(self, user_input: str) -> str:
        """
        Main method to process user input and manage conversation flow
        """
        # Check if all fields are filled
        next_field = self.get_next_missing_field()
        
        if next_field is None:
            self.save_to_csv()
            return "Thank you! Your application has been completed and saved."
        
        # Try to extract details for the current field
        extracted_value = self.extract_details(next_field, user_input)
        
        if extracted_value:
            # Special handling for name fields
            if next_field in ['first_name', 'last_name']:
                names = user_input.split()
                self.fields['first_name'] = names[0]
                if len(names) > 1:
                    self.fields['last_name'] = ' '.join(names[1:])
                    self.current_index += 1  # Skip last name
            else:
                self.fields[next_field] = extracted_value
            
            # Move to next field
            self.current_index += 1
            
            # Loop to process next field
            return self.process_next_field()
        
        # If no extraction, ask the specific question
        return self.generate_question(next_field)
    
    def process_next_field(self) -> str:
        """
        Find and generate question for the next missing field
        """
        next_field = self.get_next_missing_field()
        
        if next_field is None:
            self.save_to_csv()
            return "Thank you! Your application has been completed and saved."
        
        return self.generate_question(next_field)
    
    def save_to_csv(self):
        """
        Save collected information to a CSV file
        """
        try:
            df = pd.DataFrame([self.fields])
            df.to_csv('responses.csv', mode='a', header=not pd.io.common.file_exists('responses.csv'), index=False)
        except Exception as e:
            print(f"Error saving to CSV: {e}")

    def handle_commitments(self, user_input: str) -> str:
        """
        Handles multiple commitments by appending them to the commitments list
        """
        if self.fields['commitments'] is not None:
            self.fields['commitments'].append(user_input)
        else:
            self.fields['commitments'] = [user_input]
        self.current_index += 1
        return self.process_next_field()

    def handle_uploaded_files(self, field: str, user_input: str) -> str:
        """
        Handles file uploads (e.g., IDs, documents) by adding them to respective fields
        """
        if field == 'uploaded_ids':
            self.fields['uploaded_ids'].append(user_input)
        elif field == 'uploaded_documents':
            self.fields['uploaded_documents'].append(user_input)
        self.current_index += 1
        return self.process_next_field()
