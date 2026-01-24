<script setup lang="ts">
import { validateImageUrl } from "~/utils/urlValidation";

const imageUrl = ref("https://cdn.fairdataihub.org/gallery/2024-07-14%20-%20BOSC%202024%20Conference/PXL_20230724_170941285.jpg");
const prompt = ref("");
const loading = ref(false);
const result = ref("");
const error = ref("");

const generateAltText = async () => {
  // Clear previous errors
  error.value = "";
  result.value = "";

  // Validate URL is provided
  if (!imageUrl.value || !imageUrl.value.trim()) {
    error.value = "Please enter an image URL";
    return;
  }

  // Validate URL format and safety
  const validation = validateImageUrl(imageUrl.value.trim());
  if (!validation.isValid) {
    error.value = validation.error || "Invalid image URL";
    return;
  }

  loading.value = true;

  try {
    const response = await $fetch<string>("/api/generate", {
      method: "GET",
      query: {
        imageUrl: imageUrl.value.trim(),
        ...(prompt.value && { prompt: prompt.value.trim() }),
      },
    });

    result.value = response;
  } catch (err: any) {
    error.value = err.message || "Failed to generate alt text";
  } finally {
    loading.value = false;
  }
};

const copyToClipboard = async () => {
  if (result.value && typeof navigator !== "undefined" && navigator.clipboard) {
    await navigator.clipboard.writeText(result.value);
  }
};
</script>

<template>
  <UContainer class="flex min-h-screen items-center justify-center py-6">
    <div class="w-full max-w-2xl space-y-6">
      <div class="text-center">
        <h1 class="text-4xl font-bold">Alt Text Generator</h1>
        <p class="mt-2 text-gray-600 dark:text-gray-400">
          Enter an image URL and optional prompt to generate alt text
        </p>
      </div>

      <UCard>
        <template #header>
          <h2 class="text-xl font-semibold">Generate Alt Text</h2>
        </template>

        <div class="flex flex-col space-y-4">
          <UFormField label="Image URL" name="imageUrl" required>
            <UInput
              v-model="imageUrl"
              type="url"
              placeholder="https://example.com/image.jpg"
              :disabled="loading"
            >
              <template #trailing>
                <UButton
                  v-if="imageUrl"
                  color="neutral"
                  variant="ghost"
                  icon="i-heroicons-x-mark"
                  :padded="false"
                  @click="imageUrl = ''"
                />
              </template>
            </UInput>
          </UFormField>

          <UFormField label="Prompt (optional)" name="prompt">
            <UInput
              v-model="prompt"
              type="text"
              placeholder="Describe this image in one concise sentence for alt text."
              :disabled="loading"
            >
              <template #trailing>
                <UButton
                  v-if="prompt"
                  color="neutral"
                  variant="ghost"
                  icon="i-heroicons-x-mark"
                  :padded="false"
                  @click="prompt = ''"
                />
              </template>
            </UInput>
          </UFormField>

          <UButton
            block
            :loading="loading"
            :disabled="!imageUrl"
            @click="generateAltText"
          >
            Generate Alt Text
          </UButton>
        </div>
      </UCard>

      <UAlert v-if="error" color="error" variant="soft" :title="error" />

      <div v-if="imageUrl || result" class="grid gap-6 md:grid-cols-2">
        <UCard v-if="imageUrl">
          <template #header>
            <h3 class="text-lg font-semibold">Image Preview</h3>
          </template>
          <div class="flex items-center justify-center">
            <img
              :src="imageUrl"
              alt="Preview"
              class="max-h-96 w-full rounded-lg object-contain"
              @error="error = 'Failed to load image. Please check the URL.'"
            />
          </div>
        </UCard>

        <UCard v-if="result">
          <template #header>
            <h3 class="text-lg font-semibold">Generated Alt Text</h3>
          </template>
          <div class="space-y-2">
            <p class="text-base leading-relaxed">{{ result }}</p>
            <UButton
              color="neutral"
              variant="ghost"
              size="sm"
              icon="i-heroicons-clipboard-document"
              @click="copyToClipboard"
            >
              Copy to Clipboard
            </UButton>
          </div>
        </UCard>
      </div>
    </div>
  </UContainer>
</template>
