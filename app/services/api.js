import axios from "axios";

const API_URL = "http://localhost:8000/api";

export const captureFace = async (imageData) => {
    return axios.post(`${API_URL}/face-recognition/authenticate`, { image: imageData });
};
