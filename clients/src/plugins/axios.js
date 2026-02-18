import axios from "axios";
// import router from "@/router";

const axiosPlugin = {
    install(app) {
        const axiosInstance = axios.create({
            baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/cors',
            headers: {
                'Content-Type': 'application/json',
                // Authorization: `Bearer`
            }
        });

        axiosInstance.interceptors.request.use((config) => {
            const token = sessionStorage.getItem('token')
            if (token) {
                config.headers.Authorization = `Bearer ${token}`
            }
            return config
        })

        axiosInstance.interceptors.response.use(
            function(response) {
                return response
            },
            function(error) {
                if (error.response.status === 404) {
                    // Rediriger vers la page d'erreur 404
                }
                return Promise.reject(error);
            }
        )

        app.provide('axios', axiosInstance);
        app.config.globalProperties.$axios = axiosInstance;
    }
};

export default axiosPlugin;
