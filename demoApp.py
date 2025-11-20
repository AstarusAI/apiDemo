"""
A simple demo app in streamlit based on our alpha api!
"""
import streamlit as st
import requests

BASE_URL = "https://fhd5rgv0o0dd8i-8000.proxy.runpod.net/"
UNIQUE_NAME = "myTest02"

def generate(prompt, length=20, lut_name=None):
    payload = {
        "prompt": prompt,
        "length": length,
    }
    if lut_name is not None:
        payload["lut_name"] = lut_name

    r = requests.post(f"{BASE_URL}/generate", json=payload)
    print("Status:", r.status_code)
    print("Response:", r.json())
    return r.json()

def train_lut(label, lut_name="user_123", label_context=None):
    payload = {
        "label": label,
        "lut_name": lut_name,
        "label_context": label_context,
    }
    r = requests.post(f"{BASE_URL}/train_lut", json=payload)
    print("Status:", r.status_code)
    print("Response:", r.json())


st.set_page_config("wide", "GPT x LUTs Demo")
st.title("GPT x LUTs Demo running on our API!")

UNIQUE_NAME = st.text_input("Enter a unique ID to store your personal LUT!")


left, right = st.columns(2)

with left:
    prompt= st.text_area("Enter a prompt")
    num_tokens = st.number_input("How many tokens to generate?", min_value=0, max_value=100)
    if st.button("Run"):
        out = generate(prompt=prompt, length=num_tokens, lut_name=UNIQUE_NAME)
        st.write("Ouput: ", out["completion"])

with right:
    train_context = st.text_area("Train context: ")
    train_label = st.text_area("Train content: ")

    if st.button("Train"):
        train_lut(label=train_label, lut_name=UNIQUE_NAME, label_context=train_context)
