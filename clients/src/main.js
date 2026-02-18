import { createApp } from 'vue';
import { registerPlugins } from './plugins';

import App from './App.vue'
import './assets/style.css'
// Font Awesome core
import { library } from '@fortawesome/fontawesome-svg-core'
import { faEye, faEyeSlash } from '@fortawesome/free-solid-svg-icons'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'


library.add(faEye, faEyeSlash)

const app = createApp(App)
registerPlugins(app)
app.component('FontAwesomeIcon', FontAwesomeIcon)

app.mount('#app')
