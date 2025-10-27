# AI Models Setup Guide

The SkillMiner Agent can be enhanced with various AI models for better skill extraction and analysis.

## 🚀 Quick Setup

### 1. Enable AI Models
```bash
export SKILLMINER_USE_AI=true
```

### 2. Choose Your Models

## 🤖 Available Models

### Option 1: spaCy (Recommended for Local Use)
```bash
# Install spaCy
pip install spacy

# Download English model
python -m spacy download en_core_web_sm

# Enable spaCy
export SPACY_ENABLED=true
```

### Option 2: OpenAI API (Best Quality)
```bash
# Install OpenAI client
pip install openai

# Set API key
export OPENAI_API_KEY=your_api_key_here
export OPENAI_MODEL=gpt-3.5-turbo  # or gpt-4
```

### Option 3: Local LLM with Ollama (Privacy-Focused)
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull a model
ollama pull llama2  # or mistral, codellama

# Start Ollama server
ollama serve

# Enable in SkillMiner
export LOCAL_LLM_ENABLED=true
export LOCAL_LLM_MODEL=llama2
```

### Option 4: Hugging Face Transformers
```bash
# Install transformers
pip install transformers torch

# Enable transformers
export TRANSFORMERS_ENABLED=true

# For GPU (optional)
export TRANSFORMERS_DEVICE=cuda
```

### Option 5: Azure OpenAI
```bash
# Set Azure credentials
export AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
export AZURE_OPENAI_API_KEY=your_api_key_here
export AZURE_OPENAI_DEPLOYMENT=your_deployment_name
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SKILLMINER_USE_AI` | Enable AI models | `false` |
| `OPENAI_API_KEY` | OpenAI API key | - |
| `OPENAI_MODEL` | OpenAI model name | `gpt-3.5-turbo` |
| `LOCAL_LLM_ENABLED` | Enable local LLM | `false` |
| `LOCAL_LLM_ENDPOINT` | Ollama endpoint | `http://localhost:11434/api/generate` |
| `LOCAL_LLM_MODEL` | Local model name | `llama2` |
| `SPACY_ENABLED` | Enable spaCy | `true` |
| `TRANSFORMERS_ENABLED` | Enable transformers | `false` |

### Check Model Status
```bash
curl http://localhost:8000/api/models
```

## 📊 Performance Comparison

| Model | Speed | Quality | Privacy | Cost |
|-------|-------|---------|---------|------|
| Rule-based | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Free |
| spaCy | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Free |
| Local LLM | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Free |
| OpenAI | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | Paid |
| Transformers | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Free |

## 🎯 Recommendations

### For Development/Testing
- **spaCy**: Fast, reliable, works offline
- **Local LLM**: Good balance of quality and privacy

### For Production
- **OpenAI**: Best quality, reliable API
- **Azure OpenAI**: Enterprise-grade with compliance

### For Privacy-Sensitive Use
- **spaCy + Rule-based**: No external API calls
- **Local LLM**: All processing on your hardware

## 🔍 Testing AI Models

```python
# Test different models
from src.analyzer import SkillGapAnalyzer

# With AI models
analyzer_ai = SkillGapAnalyzer(use_ai_models=True)

# Without AI models (rule-based only)
analyzer_basic = SkillGapAnalyzer(use_ai_models=False)

# Compare results
job_desc = "Python developer with ML experience needed"
resume = "Software engineer with 3 years Python, Django, pandas"

result_ai = analyzer_ai.analyze({"job_description": job_desc, "resume_text": resume})
result_basic = analyzer_basic.analyze({"job_description": job_desc, "resume_text": resume})

print(f"AI Model Skills: {len(result_ai.existing_skills)}")
print(f"Rule-based Skills: {len(result_basic.existing_skills)}")
```

## 🛠️ Troubleshooting

### spaCy Model Not Found
```bash
python -m spacy download en_core_web_sm
```

### OpenAI API Errors
- Check API key is valid
- Verify billing is set up
- Check rate limits

### Ollama Connection Issues
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Restart Ollama
ollama serve
```

### GPU Not Detected
```bash
# Check PyTorch GPU support
python -c "import torch; print(torch.cuda.is_available())"

# Install CUDA version
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```