import { describe, it, expect, vi } from "vitest";
import { render, fireEvent, screen } from "@testing-library/react";
import { FileUploader } from "@/components/ui";

describe("FileUploader", () => {
  it("calls onFiles when files are dropped", async () => {
    const onFiles = vi.fn();
    render(<FileUploader onFiles={onFiles} multiple />);

    const dropZone = screen.getByLabelText("File upload area");
    const file = new File(["hello"], "test.txt", { type: "text/plain" });

    fireEvent.drop(dropZone, {
      dataTransfer: { files: [file] },
    });

    expect(onFiles).toHaveBeenCalledTimes(1);
    expect(onFiles.mock.calls[0][0][0].name).toBe("test.txt");
  });
});
