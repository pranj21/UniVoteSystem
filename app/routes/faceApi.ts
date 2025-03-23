export const recognizeFace = async (imageFile: File): Promise<any> => {
    const formData = new FormData();
    formData.append("file", imageFile);

    const response = await fetch("http://localhost:8000/api/face/recognize", {
        method: "POST",
        body: formData,
    });

    return response.json();
};
