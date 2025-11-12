# AmaniQuery API - Vercel Deployment

This is the FastAPI backend for AmaniQuery, configured for deployment on Vercel.

## Local Development

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Run the API:

   ```bash
   python -m uvicorn Module4_NiruAPI.api:app --reload
   ```

3. Access the API at `http://localhost:8000`

## Vercel Deployment

### Prerequisites

1. A Vercel account
2. Your GitHub repository connected to Vercel
3. Required environment variables configured

### Deployment Steps

1. **Connect Repository to Vercel**
   - Go to [vercel.com](https://vercel.com)
   - Click "New Project"
   - Import your `amaniquery` repository
   - Configure the project:
     - **Framework Preset**: Other
     - **Root Directory**: `Module4_NiruAPI`
     - **Build Command**: `pip install -r requirements.txt`
     - **Output Directory**: (leave empty)

2. **Set Environment Variables**
   In the Vercel dashboard, add these environment variables:

   **Required:**
   - `CORS_ORIGINS`: `https://amaniquery.vercel.app` (your frontend URL)
   - `LLM_PROVIDER`: Your LLM provider (e.g., `moonshot`, `openai`, `anthropic`)
   - `DEFAULT_MODEL`: Your model name
   - `EMBEDDING_MODEL`: Your embedding model

   **Optional (but recommended):**
   - `OPENAI_API_KEY`: If using OpenAI
   - `ANTHROPIC_API_KEY`: If using Anthropic
   - `GEMINI_API_KEY`: If using Gemini
   - Database connection strings if using external DB

3. **Deploy**
   - Click "Deploy"
   - Wait for the build to complete
   - Your API will be available at `https://api-amaniquery.vercel.app`

### Important Notes

- **Cold Starts**: Vercel has a 10-second cold start limit. The first request after inactivity may be slow.
- **Database**: Ensure your ChromaDB and PostgreSQL databases are accessible from Vercel's servers.
- **File Storage**: Consider using cloud storage for persistent file storage.
- **Environment Variables**: All sensitive keys should be set as environment variables, not in code.

## API Endpoints

Once deployed, your API will be available with these endpoints:

- `GET /` - API information
- `GET /health` - Health check
- `GET /stats` - Database statistics
- `POST /query` - Main query endpoint
- `POST /chat/sessions` - Create chat sessions
- And many more...

Full API documentation available at `/docs` when running locally.

## Troubleshooting

- **Build fails**: Check that all dependencies in `requirements.txt` are compatible with Vercel's Python runtime
- **API errors**: Check Vercel function logs for detailed error messages
- **CORS issues**: Verify the `CORS_ORIGINS` environment variable matches your frontend URL
- **Database connection**: Ensure your database allows connections from Vercel's IP ranges
