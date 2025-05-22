import { createPinia } from 'pinia';
// Potentially import and register your store if not auto-done by structure
// import { useRawQuestionStore } from './rawQuestionStore';

const pinia = createPinia();

export default pinia;
// If you need to use stores outside components, you might initialize them here after pinia is created.
