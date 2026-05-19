<template>
  <div class="login-layout">
    <!-- Background watermark text - positioned at top -->
    <div class="bg-watermark">
      <span class="watermark-main">个人</span><span class="watermark-accent">Office</span><span class="watermark-main">办公助手</span>
    </div>

    <!-- Centered Login Card -->
    <div class="login-card">
      <!-- Login Card -->
      <div v-if="!isRegisterMode" class="form-card">
        <div class="form-header">
          <div class="logo-row">
            <span class="logo-text-main">个人</span><span class="logo-text-accent">Office</span><span class="logo-text-main">办公助手</span>
          </div>
          <h2 class="form-title">{{ $t('auth.login') }}</h2>
          <p class="form-subtitle">{{ $t('auth.subtitle') }}</p>
        </div>

        <t-form
          ref="formRef"
          :data="formData"
          :rules="formRules"
          @submit="handleLogin"
          layout="vertical"
        >
          <t-form-item :label="$t('auth.email')" name="email">
            <t-input
              v-model="formData.email"
              :placeholder="$t('auth.emailPlaceholder')"
              type="email"
              size="large"
              :disabled="loading"
            />
          </t-form-item>

          <t-form-item :label="$t('auth.password')" name="password">
            <t-input
              v-model="formData.password"
              :placeholder="$t('auth.passwordPlaceholder')"
              type="password"
              size="large"
              :disabled="loading"
              @keydown.enter="handleLogin"
            />
          </t-form-item>

          <t-button
            type="submit"
            theme="primary"
            size="large"
            block
            :loading="loading"
            class="submit-button"
          >
            {{ loading ? $t('auth.loggingIn') : $t('auth.login') }}
          </t-button>
        </t-form>

        <div class="form-footer">
          <span>{{ $t('auth.noAccount') }}</span>
          <a href="#" @click.prevent="toggleMode" class="link-button">
            {{ $t('auth.registerNow') }}
          </a>
        </div>

        <template v-if="oidcEnabled">
          <div class="oidc-divider">
            <span>{{ $t('auth.orContinueWith') }}</span>
          </div>
          <t-button
            theme="default"
            size="large"
            block
            :loading="oidcLoading"
            :disabled="loading"
            class="oidc-button"
            @click="handleOIDCLogin"
          >
            {{ oidcLoading ? $t('auth.redirectingToOIDC') : oidcLoginText }}
          </t-button>
        </template>
      </div>

      <!-- Register Card -->
      <div v-if="isRegisterMode" class="form-card">
        <div class="form-header">
          <div class="logo-row">
            <span class="logo-text-main">个人</span><span class="logo-text-accent">Office</span><span class="logo-text-main">办公助手</span>
          </div>
          <h2 class="form-title">{{ $t('auth.createAccount') }}</h2>
          <p class="form-subtitle">{{ $t('auth.registerSubtitle') }}</p>
        </div>

        <t-form
          ref="registerFormRef"
          :data="registerData"
          :rules="registerRules"
          @submit="handleRegister"
          layout="vertical"
        >
          <t-form-item :label="$t('auth.username')" name="username">
            <t-input
              v-model="registerData.username"
              :placeholder="$t('auth.usernamePlaceholder')"
              size="large"
              :disabled="loading"
            />
          </t-form-item>

          <t-form-item :label="$t('auth.email')" name="email">
            <t-input
              v-model="registerData.email"
              :placeholder="$t('auth.emailPlaceholder')"
              type="email"
              size="large"
              :disabled="loading"
            />
          </t-form-item>

          <t-form-item :label="$t('auth.password')" name="password">
            <t-input
              v-model="registerData.password"
              :placeholder="$t('auth.passwordPlaceholder')"
              type="password"
              size="large"
              :disabled="loading"
            />
          </t-form-item>

          <t-form-item :label="$t('auth.confirmPassword')" name="confirmPassword">
            <t-input
              v-model="registerData.confirmPassword"
              :placeholder="$t('auth.confirmPasswordPlaceholder')"
              type="password"
              size="large"
              :disabled="loading"
              @keydown.enter="handleRegister"
            />
          </t-form-item>

          <t-button
            type="submit"
            theme="primary"
            size="large"
            block
            :loading="loading"
            class="submit-button"
          >
            {{ loading ? $t('auth.registering') : $t('auth.register') }}
          </t-button>
        </t-form>

        <div class="form-footer">
          <span>{{ $t('auth.haveAccount') }}</span>
          <a href="#" @click.prevent="toggleMode" class="link-button">
            {{ $t('auth.backToLogin') }}
          </a>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, nextTick, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { MessagePlugin } from 'tdesign-vue-next'
import { login, register, getOIDCAuthorizationURL, getOIDCConfig, autoSetup } from '@/api/auth'
import { useAuthStore } from '@/stores/auth'
import { useI18n } from 'vue-i18n'

const router = useRouter()
const authStore = useAuthStore()
const { t } = useI18n()

// Form references
const formRef = ref()
const registerFormRef = ref()

// State management
const loading = ref(false)
const oidcLoading = ref(false)
const isRegisterMode = ref(false)
const oidcEnabled = ref(false)
const oidcProviderName = ref('')

const oidcLoginText = computed(() => {
  if (oidcProviderName.value) {
    return t('auth.oidcLoginWithProvider', { provider: oidcProviderName.value })
  }
  return t('auth.oidcLogin')
})

// Login form data
const formData = reactive<{[key: string]: any}>({
  email: '',
  password: '',
})

// Register form data
const registerData = reactive<{[key: string]: any}>({
  username: '',
  email: '',
  password: '',
  confirmPassword: ''
})

// Login form validation rules
const formRules = computed(() => ({
  email: [
    { required: true, message: t('auth.emailRequired'), type: 'error' },
    { email: true, message: t('auth.emailInvalid'), type: 'error' }
  ],
  password: [
    { required: true, message: t('auth.passwordRequired'), type: 'error' },
    { min: 8, message: t('auth.passwordMinLength'), type: 'error' },
    { max: 32, message: t('auth.passwordMaxLength'), type: 'error' },
    { pattern: /[a-zA-Z]/, message: t('auth.passwordMustContainLetter'), type: 'error' },
    { pattern: /\d/, message: t('auth.passwordMustContainNumber'), type: 'error' }
  ]
}))

// Register form validation rules
const registerRules = computed(() => ({
  username: [
    { required: true, message: t('auth.usernameRequired'), type: 'error' },
    { min: 2, message: t('auth.usernameMinLength'), type: 'error' },
    { max: 20, message: t('auth.usernameMaxLength'), type: 'error' },
    {
      pattern: /^[a-zA-Z0-9_\u4e00-\u9fa5]+$/,
      message: t('auth.usernameInvalid'),
      type: 'error'
    }
  ],
  email: [
    { required: true, message: t('auth.emailRequired'), type: 'error' },
    { email: true, message: t('auth.emailInvalid'), type: 'error' }
  ],
  password: [
    { required: true, message: t('auth.passwordRequired'), type: 'error' },
    { min: 8, message: t('auth.passwordMinLength'), type: 'error' },
    { max: 32, message: t('auth.passwordMaxLength'), type: 'error' },
    { pattern: /[a-zA-Z]/, message: t('auth.passwordMustContainLetter'), type: 'error' },
    { pattern: /\d/, message: t('auth.passwordMustContainNumber'), type: 'error' }
  ],
  confirmPassword: [
    { required: true, message: t('auth.confirmPasswordRequired'), type: 'error' },
    {
      validator: (val: string) => val === registerData.password,
      message: t('auth.passwordMismatch'),
      type: 'error'
    }
  ]
}))

// Toggle login/register mode
const toggleMode = () => {
  isRegisterMode.value = !isRegisterMode.value
  Object.keys(registerData).forEach(key => {
    (registerData as any)[key] = ''
  })
}

const persistLoginResponse = async (response: any) => {
  if (response.user && response.tenant && response.token) {
    authStore.setUser({
      id: response.user.id || '',
      username: response.user.username || '',
      email: response.user.email || '',
      avatar: response.user.avatar,
      tenant_id: String(response.tenant.id) || '',
      can_access_all_tenants: response.user.can_access_all_tenants || false,
      created_at: response.user.created_at || new Date().toISOString(),
      updated_at: response.user.updated_at || new Date().toISOString()
    })
    authStore.setToken(response.token)
    if (response.refresh_token) {
      authStore.setRefreshToken(response.refresh_token)
    }
    authStore.setTenant({
      id: String(response.tenant.id) || '',
      name: response.tenant.name || '',
      api_key: response.tenant.api_key || '',
      owner_id: response.user.id || '',
      created_at: response.tenant.created_at || new Date().toISOString(),
      updated_at: response.tenant.updated_at || new Date().toISOString()
    })
  }

  await nextTick()
  router.replace('/platform/knowledge-bases')
}

const getBackendOIDCRedirectURI = () => `${window.location.origin}/api/v1/auth/oidc/callback`

const loadOIDCConfig = async () => {
  try {
    const response = await getOIDCConfig()
    oidcEnabled.value = !!response.success && !!response.enabled
    oidcProviderName.value = response.provider_display_name || ''
  } catch {
    oidcEnabled.value = false
    oidcProviderName.value = ''
  }
}

const handleOIDCLogin = async () => {
  try {
    oidcLoading.value = true
    const response = await getOIDCAuthorizationURL(getBackendOIDCRedirectURI())
    const authorizationURL = response.authorization_url

    if (!response.success || !authorizationURL) {
      MessagePlugin.error(response.message || t('auth.oidcLoginFailed'))
      return
    }

    window.location.href = authorizationURL
  } catch (error: any) {
    console.error('OIDC 登录跳转失败:', error)
    MessagePlugin.error(error.message || t('auth.oidcLoginFailed'))
  } finally {
    oidcLoading.value = false
  }
}

// Handle login
const handleLogin = async () => {
  try {
    const valid = await formRef.value?.validate()
    if (valid !== true) return

    loading.value = true

    const response = await login({
      email: formData.email,
      password: formData.password,
    })

    if (response.success) {
      MessagePlugin.success(t('auth.loginSuccess'))
      await persistLoginResponse(response)
    } else {
      MessagePlugin.error(response.message || t('auth.loginError'))
    }
  } catch (error: any) {
    console.error('登录错误:', error)
    MessagePlugin.error(error.message || t('auth.loginErrorRetry'))
  } finally {
    loading.value = false
  }
}

// Handle registration
const handleRegister = async () => {
  try {
    const valid = await registerFormRef.value?.validate()
    if (valid !== true) return

    loading.value = true

    const response = await register({
      username: registerData.username,
      email: registerData.email,
      password: registerData.password
    })

    if (response.success) {
      MessagePlugin.success(t('auth.registerSuccess'))
      isRegisterMode.value = false
      formData.email = registerData.email

      Object.keys(registerData).forEach(key => {
        (registerData as any)[key] = ''
      })
    } else {
      MessagePlugin.error(response.message || t('auth.registerFailed'))
    }
  } catch (error: any) {
    console.error('注册错误:', error)
    MessagePlugin.error(error.message || t('auth.registerError'))
  } finally {
    loading.value = false
  }
}

// Check if already logged in; for lite edition, attempt transparent auto-setup
onMounted(async () => {
  if (authStore.isLoggedIn) {
    router.replace('/platform/knowledge-bases')
    return
  }

  const AUTO_SETUP_FAILED_KEY = 'weknora_auto_setup_failed'
  if (localStorage.getItem(AUTO_SETUP_FAILED_KEY) !== 'true') {
    try {
      const response = await autoSetup()
      if (response.success) {
        authStore.setLiteMode(true)
        await persistLoginResponse(response)
        return
      } else {
        localStorage.setItem(AUTO_SETUP_FAILED_KEY, 'true')
      }
    } catch {
      localStorage.setItem(AUTO_SETUP_FAILED_KEY, 'true')
    }
  }

  loadOIDCConfig()
})
</script>

<style lang="less" scoped>
.login-layout {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  min-height: 100%;
  overflow: hidden;
  position: relative;
  background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 25%, #bbf7d0 50%, #86efac 75%, #4ade80 100%);
}

/* Background watermark text - top area */
.bg-watermark {
  position: absolute;
  top: 8%;
  left: 50%;
  transform: translateX(-50%);
  z-index: 0;
  pointer-events: none;
  user-select: none;
  white-space: nowrap;
  display: flex;
  align-items: baseline;
  font-family: "TencentSans", "PingFang SC", "Microsoft YaHei", sans-serif;
  font-size: clamp(36px, 5vw, 72px);
  font-weight: 700;
  letter-spacing: 4px;
  line-height: 1;
  opacity: 0.15;
}

.watermark-main {
  color: var(--td-text-color-primary, #1a1a1a);
}

.watermark-accent {
  color: var(--td-brand-color, #07C05F);
  margin: 0 4px;
}

/* Centered Login Card */
.login-card {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 420px;
  padding: 0 24px;
  box-sizing: border-box;
}

.form-card {
  background: rgba(255, 255, 255, 0.88);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-radius: 20px;
  padding: 40px 36px;
  box-shadow:
    0 8px 32px rgba(0, 0, 0, 0.08),
    0 2px 8px rgba(0, 0, 0, 0.04);
  box-sizing: border-box;
  border: 1px solid rgba(255, 255, 255, 0.6);
}

.form-header {
  text-align: center;
  margin-bottom: 28px;
}

.logo-row {
  display: flex;
  justify-content: center;
  align-items: baseline;
  margin-bottom: 16px;
  font-family: "TencentSans", "PingFang SC", "Microsoft YaHei", sans-serif;
  font-size: 20px;
  font-weight: 700;
  letter-spacing: 1px;
}

.logo-text-main {
  color: var(--td-text-color-primary);
}

.logo-text-accent {
  color: var(--td-brand-color);
  margin: 0 2px;
}

.form-title {
  font-size: 22px;
  font-weight: 600;
  color: var(--td-text-color-primary);
  margin: 0 0 6px 0;
  font-family: var(--app-font-family);
}

.form-subtitle {
  font-size: 13px;
  color: var(--td-text-color-secondary);
  margin: 0;
  font-family: var(--app-font-family);
}

:deep(.t-form-item__label) {
  font-size: 14px;
  color: var(--td-text-color-primary);
  font-weight: 500;
  margin-bottom: 6px;
  font-family: var(--app-font-family);
  display: block;
  text-align: left;
}

:deep(.t-input) {
  border: 1px solid var(--td-component-stroke);
  border-radius: 8px;
  background: var(--td-bg-color-container);
  transition: all 0.2s;

  &:focus-within {
    border-color: var(--td-brand-color);
    box-shadow: 0 0 0 3px rgba(7, 192, 95, 0.1);
  }

  &:hover {
    border-color: var(--td-brand-color);
  }

  .t-input__inner {
    border: none !important;
    box-shadow: none !important;
    outline: none !important;
    background: transparent;
    font-size: 15px;
    font-family: var(--app-font-family);

    &:focus {
      border: none !important;
      box-shadow: none !important;
      outline: none !important;
    }
  }

  .t-input__wrap {
    border: none !important;
    box-shadow: none !important;
  }
}

:deep(.t-form-item) {
  margin-bottom: 16px;
}

:deep(.t-form-item__control) {
  width: 100%;
}

.submit-button {
  height: 46px;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 500;
  font-family: var(--app-font-family);
  margin: 20px 0 16px 0;
}

.oidc-divider {
  position: relative;
  margin: 8px 0;
  text-align: center;
  color: var(--td-text-color-placeholder);
  font-size: 12px;

  span {
    position: relative;
    z-index: 1;
    padding: 0 12px;
    background: rgba(255, 255, 255, 0.88);
  }

  &::before {
    content: '';
    position: absolute;
    left: 0;
    right: 0;
    top: 50%;
    border-top: 1px solid var(--td-component-stroke);
  }
}

.oidc-button {
  height: 46px;
  border-radius: 8px;
  font-size: 15px;
  font-weight: 500;
}

.form-footer {
  text-align: center;
  font-size: 14px;
  color: var(--td-text-color-secondary);
  font-family: var(--app-font-family);
  margin-top: 16px;

  .link-button {
    color: var(--td-brand-color);
    text-decoration: none;
    margin-left: 4px;
    font-weight: 500;
    transition: all 0.2s;

    &:hover {
      color: var(--td-brand-color);
      text-decoration: underline;
    }
  }
}

/* Responsive Design */
@media (max-width: 768px) {
  .bg-watermark {
    font-size: clamp(24px, 4vw, 48px);
    opacity: 0.1;
  }

  .login-card {
    max-width: 360px;
  }

  .form-card {
    padding: 32px 24px;
  }
}

@media (max-width: 480px) {
  .bg-watermark {
    font-size: clamp(20px, 3.5vw, 36px);
    opacity: 0.08;
  }

  .logo-row {
    font-size: 18px;
  }

  .login-card {
    padding: 0 16px;
  }

  .form-card {
    padding: 28px 20px;
    border-radius: 16px;
  }

  .form-title {
    font-size: 20px;
  }
}
</style>

<style lang="less">
html[theme-mode="dark"] {
  .login-layout {
    background: linear-gradient(135deg, #052e16 0%, #064e3b 25%, #065f46 50%, #047857 75%, #059669 100%);
  }

  .bg-watermark {
    opacity: 0.1;
  }

  .watermark-main {
    color: rgba(255, 255, 255, 0.9);
  }

  .watermark-accent {
    color: #34D399;
  }

  .form-card {
    background: rgba(30, 30, 30, 0.92) !important;
    border-color: rgba(255, 255, 255, 0.08) !important;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3), 0 2px 8px rgba(0, 0, 0, 0.2) !important;
  }

  .form-card .t-input {
    background: var(--td-bg-color-page) !important;
    border-color: rgba(255, 255, 255, 0.1) !important;

    &:hover { border-color: var(--td-brand-color) !important; }
    &:focus-within { border-color: var(--td-brand-color) !important; }
  }

  .oidc-divider span {
    background: rgba(30, 30, 30, 0.92) !important;
  }
}
</style>
