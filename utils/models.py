from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.ollama import OllamaProvider

llama3_2_ollama_model = OpenAIChatModel(
    model_name='llama3.2',
    provider=OllamaProvider(base_url='http://localhost:11434/v1'),
)


tinyllama_model = OpenAIChatModel(
    model_name='tinyllama:latest',
    provider=OllamaProvider(base_url='http://localhost:11434/v1'),
)

gpt_4o_openai_model = "openai:gpt-4o"


llama3_ollama_model = OpenAIChatModel(
    model_name='llama3:latest',
    provider=OllamaProvider(base_url='http://localhost:11434/v1'),
)


deepstreamr1_8b_model = OpenAIChatModel(
    model_name='deepseek-r1:8b',
    provider=OllamaProvider(base_url='http://localhost:11434/v1'),
)


deepstream_r1_32b_model = OpenAIChatModel(
    model_name='deepseek-r1:32b',
    provider=OllamaProvider(base_url='http://localhost:11434/v1'),
)

gemma3_12b_model = OpenAIChatModel(
    model_name='gemma3:12b',
    provider=OllamaProvider(base_url='http://localhost:11434/v1'),
)

gemma3_27b_model = OpenAIChatModel(
    model_name='gemma3:27b',
    provider=OllamaProvider(base_url='http://localhost:11434/v1'),
)

gemma3_27b_it_qat_model = OpenAIChatModel(
    model_name='gemma3:27b-it-qat',
    provider=OllamaProvider(base_url='http://localhost:11434/v1'),
)


mixtral_8x7b_model = OpenAIChatModel(
    model_name='mixtral:8x7b',
    provider=OllamaProvider(base_url='http://localhost:11434/v1'),
)


qwen3_32b_model = OpenAIChatModel(
    model_name='qwen3:32b',
    provider=OllamaProvider(base_url='http://localhost:11434/v1'),
)


gpt_oss_20b_model = OpenAIChatModel(
    model_name='gpt-oss:20b',
    provider=OllamaProvider(base_url='http://10.239.222.81:11434/v1'),
)

#http://172.31.0.8:9105/v1