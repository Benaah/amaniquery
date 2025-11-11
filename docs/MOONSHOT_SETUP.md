# Moonshot AI Configuration Guide

## About Moonshot AI

Moonshot AI (月之暗面) is a Chinese AI company that provides powerful language models with competitive pricing and performance. AmaniQuery uses Moonshot AI as the default LLM provider.

## Getting Started

### 1. Create Account

Visit: https://platform.moonshot.cn/

- Sign up for an account
- Verify your email/phone
- Complete account setup

### 2. Get API Key

1. Login to https://platform.moonshot.cn/console
2. Navigate to "API Keys" section
3. Click "Create New Key"
4. Copy your API key
5. Add to `.env` file:

```env
MOONSHOT_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxx
MOONSHOT_BASE_URL=https://api.moonshot.cn/v1
```

## Available Models

### moonshot-v1-8k (Default)
- **Context Window:** 8,192 tokens
- **Best For:** Quick queries, cost-effective
- **Speed:** Fastest
- **Cost:** Lowest

### moonshot-v1-32k
- **Context Window:** 32,768 tokens
- **Best For:** Longer documents, detailed analysis
- **Speed:** Medium
- **Cost:** Medium

### moonshot-v1-128k
- **Context Window:** 131,072 tokens
- **Best For:** Very long documents, comprehensive research
- **Speed:** Slower
- **Cost:** Highest

## Switching Models

Edit `.env`:

```env
DEFAULT_MODEL=moonshot-v1-32k  # Change to desired model
```

## Pricing (As of 2025)

- **moonshot-v1-8k:** ~¥0.012/1K tokens
- **moonshot-v1-32k:** ~¥0.024/1K tokens
- **moonshot-v1-128k:** ~¥0.060/1K tokens

(Check official website for current pricing)

## API Compatibility

Moonshot AI uses OpenAI-compatible API format, so you can:
- Use the `openai` Python package
- Switch between Moonshot and OpenAI easily
- Use familiar API patterns

## Using Alternative Providers

### Switch to OpenAI

Edit `.env`:
```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-openai-key
DEFAULT_MODEL=gpt-3.5-turbo
```

### Switch to Anthropic (Claude)

Edit `.env`:
```env
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-your-key
DEFAULT_MODEL=claude-3-sonnet-20240229
```

## Troubleshooting

### Connection Issues

If you get connection errors:

1. Check your internet connection
2. Verify API key is correct
3. Ensure `MOONSHOT_BASE_URL` is set to `https://api.moonshot.cn/v1`
4. Check if you have sufficient credits

### Rate Limits

Moonshot AI has rate limits:
- Free tier: Limited requests per minute
- Paid tier: Higher limits

If you hit rate limits:
- Add delays between requests
- Upgrade to paid tier
- Reduce `top_k` in queries

### Language Support

Moonshot AI excels at:
- Chinese language understanding
- English language understanding
- Mixed Chinese-English content

Perfect for AmaniQuery's Kenyan content with potential Chinese tech/policy news.

## Performance Optimization

### For Faster Responses
```env
DEFAULT_MODEL=moonshot-v1-8k
MAX_TOKENS=1000
TEMPERATURE=0.5
```

### For Higher Quality
```env
DEFAULT_MODEL=moonshot-v1-32k
MAX_TOKENS=2000
TEMPERATURE=0.7
```

### For Maximum Context
```env
DEFAULT_MODEL=moonshot-v1-128k
MAX_TOKENS=4000
TEMPERATURE=0.7
```

## Resources

- **Official Website:** https://www.moonshot.cn/
- **API Documentation:** https://platform.moonshot.cn/docs
- **Console:** https://platform.moonshot.cn/console
- **Pricing:** https://platform.moonshot.cn/pricing

## Support

For Moonshot AI issues:
- Email: support@moonshot.cn
- Documentation: Check official docs
- Community: Moonshot AI developer forums

For AmaniQuery integration issues:
- Check logs in `logs/` directory
- Review Module 4 README
- Verify `.env` configuration
