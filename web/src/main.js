import './styles/tokens.css'
import './styles/components.css'
import './styles/theme.css'
import './styles/global.css'

import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import { setRequestRouter } from './api/request'

setRequestRouter(router)

createApp(App).use(router).mount('#app')
