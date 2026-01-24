<script setup lang="ts">
import { validateImageUrl } from "~/utils/urlValidation";

const imageUrl = ref("");
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
            />
          </UFormField>

          <UFormField label="Prompt (optional)" name="prompt">
            <UInput
              v-model="prompt"
              type="text"
              placeholder="Describe this image in one concise sentence for alt text."
              :disabled="loading"
            />
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

      <UCard v-if="result">
        <template #header>
          <h3 class="text-lg font-semibold">Generated Alt Text</h3>
        </template>
        <p>{{ result }}</p>
      </UCard>
    </div>
  </UContainer>
</template>
