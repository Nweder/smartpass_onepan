# Set up a Python environment using Anaconda
FROM continuumio/miniconda3

# Copy environment.yml to the container
COPY environment.yml /tmp/environment.yml

# Install with mamba for faster dependency resolution
RUN conda install -n base -c conda-forge mamba && \
    mamba env create -f /tmp/environment.yml --override-channels -c conda-forge --channel-priority flexible

# Set the working directory in the container to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Make port 8501 available to the world outside this container
EXPOSE 8501

# Run the application using streamlit
CMD ["conda", "run", "--no-capture-output", "-n", "dpp_app", "streamlit", "run", "src/main.py", "--server.port=8501"]