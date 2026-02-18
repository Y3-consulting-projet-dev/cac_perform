import { createPinia } from "pinia";
import router from "@/router";
import axiosPlugin from "./axios";

// CSS files
import '@mdi/font/css/materialdesignicons.css'
import '../assets/style.css'

// Gblobal components
import 'notyf/notyf.min.css'

export function registerPlugins(app) {
    app
        .use(axiosPlugin)
        .use(createPinia())
        .use(router)
}