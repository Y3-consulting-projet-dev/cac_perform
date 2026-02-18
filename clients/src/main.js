import { createApp } from 'vue';
import { registerPlugins } from './plugins';

import App from './App.vue'
import './assets/style.css'
// Font Awesome core
import { library } from '@fortawesome/fontawesome-svg-core'

// Font Awesome Vue component
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'


const app = createApp(App)
registerPlugins(app)

app.mount('#app')
