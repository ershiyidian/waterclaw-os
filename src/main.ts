import { createApp } from 'vue';
import { createPinia } from 'pinia';
import 'leaflet/dist/leaflet.css';
import './styles/tokens.css';
import './styles/reset.css';
import './styles/themes/dark.css';
import './styles/animations.css';
import './styles/layout.css';
import './styles/map.css';
import App from './App.vue';

const app = createApp(App);
app.use(createPinia());
app.mount('#app');
