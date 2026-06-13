import { createRouter, createWebHistory } from 'vue-router';
import { useAuthStore } from './authStore';
import { adminRoles, defaultRouteForRole, learningRoles } from './permissions';
import AuthLayout from '../layouts/AuthLayout.vue';
import LearningLayout from '../layouts/LearningLayout.vue';
import AdminLayout from '../layouts/AdminLayout.vue';
import LoginView from '../modules/auth/LoginView.vue';
import DashboardView from '../modules/learning/DashboardView.vue';
import JourneyView from '../modules/learning/JourneyView.vue';
import ReaderView from '../modules/learning/ReaderView.vue';
import FeedbackView from '../modules/learning/FeedbackView.vue';
import ReflectionsView from '../modules/learning/ReflectionsView.vue';
import AdminDashboard from '../modules/admin/AdminDashboard.vue';
import ContentWorkspace from '../modules/admin/ContentWorkspace.vue';
import UserManagement from '../modules/admin/UserManagement.vue';
import SubscriptionSettings from '../modules/admin/SubscriptionSettings.vue';
import MediaLibrary from '../modules/admin/MediaLibrary.vue';

const routes = [
  {
    path: '/',
    redirect: '/learn',
  },
  {
    path: '/login',
    component: AuthLayout,
    meta: { public: true },
    children: [
      {
        path: '',
        name: 'login',
        component: LoginView,
      },
    ],
  },
  {
    path: '/',
    component: LearningLayout,
    meta: { roles: learningRoles },
    children: [
      { path: 'learn', name: 'learn', component: DashboardView },
      { path: 'journey', name: 'journey', component: JourneyView },
      { path: 'reader/:chapterId?', name: 'reader', component: ReaderView },
      { path: 'feedback', name: 'feedback', component: FeedbackView },
      { path: 'reflections', name: 'reflections', component: ReflectionsView },
    ],
  },
  {
    path: '/admin',
    component: AdminLayout,
    meta: { roles: adminRoles },
    children: [
      { path: '', name: 'admin', component: AdminDashboard, meta: { roles: ['super_admin'] } },
      { path: 'content', name: 'admin-content', component: ContentWorkspace },
      { path: 'users', name: 'admin-users', component: UserManagement, meta: { roles: ['super_admin'] } },
      { path: 'subscription', name: 'admin-subscription', component: SubscriptionSettings, meta: { roles: ['super_admin'] } },
      { path: 'media', name: 'admin-media', component: MediaLibrary },
    ],
  },
];

export const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior() {
    return { top: 0 };
  },
});

router.beforeEach((to) => {
  const auth = useAuthStore();
  auth.clearInvalidSession();

  const isPublic = to.matched.some((record) => record.meta.public);
  const roleRequirements = to.matched
    .map((record) => record.meta.roles)
    .filter((roles) => roles?.length);

  if (isPublic) {
    if (auth.isAuthenticated && to.name === 'login') {
      return defaultRouteForRole(auth.user?.role);
    }
    return true;
  }

  if (!auth.isAuthenticated) {
    return {
      path: '/login',
      query: { redirect: to.fullPath },
    };
  }

  if (roleRequirements.some((roles) => !auth.hasAnyRole(roles))) {
    return defaultRouteForRole(auth.user?.role);
  }

  return true;
});
