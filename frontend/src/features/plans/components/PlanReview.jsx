import { useState } from "react";
import { Button, Group, Stack, Textarea } from "@mantine/core";

export function PlanReview({ plan, busy, onSave }) {
  const [review, setReview] = useState(plan.review || "");
  const changed = review !== (plan.review || "");

  function submit(event) {
    event.preventDefault();
    if (busy || !changed) return;
    onSave({ review });
  }

  return (
    <form onSubmit={submit}>
      <Stack gap="sm">
        <Textarea
          label="Результат"
          minRows={4}
          maxLength={50000}
          value={review}
          placeholder="Что получилось"
          onChange={(event) => setReview(event.target.value)}
        />
        <Group justify="flex-end">
          <Button type="submit" variant="filled" loading={busy} disabled={!changed}>
            Сохранить результат
          </Button>
        </Group>
      </Stack>
    </form>
  );
}
