# Antares Murmurs

![Antares Murmurs Demo](https://media4.giphy.com/media/v1.Y2lkPTc5MGI3NjExN291YzVyYXI3NXJzY29zbXZuY2NvNTJ4ZXN0ZXF4MnAzdDZ3NGVqaCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/2dMR27Z7ipMkM/giphy.gif)

## About the Project

Sometimes, the best way to understand and process our emotions is to visualize them. *Antares Murmurs* is your guide in this journey—an interactive experience that helps you explore your feelings by connecting them with the stars. Whether you’re lost in thought, overwhelmed, or seeking inspiration, this project transforms emotions into celestial stories, weaving together astronomy, artificial intelligence, storytelling and music to create a deeply personal experience.

**Antares Murmurs** allows users to describe their current emotional state, and the system matches them with a star whose scientific properties, mythology, and symbolic meaning resonate with their feelings. 

## Current Features
- **Star Data Retrieval**: Fetches real-time star data from the **SIMBAD Astronomical Database**.
- **Processed Star Characteristics**: Calculated additional stellar parameters and ensured proper transmission of essential star properties.
- **AI-Generated Mythology**: GPT-4o analyzes mythology and symbolism for selected stars.
- **Caching with Redis**: Frequently accessed star data and mythology descriptions are cached for performance optimization.
- **Database Storage**: PostgreSQL stores filtered star data and emotion mappings for efficient retrieval.
- **API Endpoints**: FastAPI-based backend provides structured responses for frontend integration.

## Planned Enhancements
- **Improved Emotion Mapping**: Refining the algorithm for deeper and more nuanced emotional analysis. Implementing FAISS to store and search emotions in a high-dimensional vector space.
- **Dynamic Star Selection**: Enhancing the matching logic to consider pulsation, brightness variation, and spectral details.
- **User Interaction Features**: Enabling users to explore personal star histories and save their matched stars.
- **Frontend Development**: Building a web interface for a seamless user experience.
- **Music & Visual Effects**: Integrating Spotify API for mood-based music selection and WebGL for visualizations.
- **Deployment**: Dockerized and planned for AWS deployment.

## Contribution

Have ideas or suggestions to improve the project? Feel free to reach out and share your thoughts!

## Technologies Used
- **Python (FastAPI, SQLAlchemy, aioredis, asyncio)**
- **OpenAI GPT-4o for mythology generation**
- **SIMBAD API for star data retrieval**
- **PostgreSQL for structured data storage**
- **Redis for caching responses**
- **FAISS for fast star similarity search using vector representations**
- **Docker for containerization (planned)**

---

💡 *"The stars are a reflection of our emotions, and Antares Murmurs brings them to life."* ✨

