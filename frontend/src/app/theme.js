import { createTheme, Button, Select, MultiSelect, TextInput, FileInput, Textarea } from "@mantine/core";

export const theme = createTheme({
  primaryColor: "blue",
  defaultRadius: "md",
  fontFamily: "Inter, system-ui, sans-serif",
  components: {
    Button: Button.extend({ defaultProps: { size: "sm", variant: "default" } }),
    Select: Select.extend({ defaultProps: { size: "sm" } }),
    MultiSelect: MultiSelect.extend({ defaultProps: { size: "sm" } }),
    TextInput: TextInput.extend({ defaultProps: { size: "sm" } }),
    FileInput: FileInput.extend({ defaultProps: { size: "sm" } }),
    Textarea: Textarea.extend({ defaultProps: { autosize: true, minRows: 4 } }),
  },
});
