export default defineAppConfig({
  ui: {
    button: {
      defaultVariants: {
        size: "lg",
      },
      slots: {
        base: "cursor-pointer rounded-lg",
      },
    },
    colors: {
      neutral: "zinc",
      primary: "pink",
    },
    input: {
      slots: {
        root: "w-full",
      },
    },
    link: {
      base: "hover:underline",
      variants: {
        active: {
          false: "text-primary-500",
        },
      },
      compoundVariants: [
        {
          active: false,
          disabled: false,
          class: ["hover:text-primary-600", "transition-all"],
        },
      ],
    },
  },
});
