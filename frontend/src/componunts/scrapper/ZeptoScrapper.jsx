import React, { useState } from "react";
import {
    Card,
    CardBody,
    Input,
    Button,
    Typography,
} from "@material-tailwind/react";
import api from "../../utils/Api";

const ZeptoScrapper = () => {
    const [searchTerm, setSearchTerm] = useState("");
    const [pages, setPages] = useState(1);
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState(null);
    const [error, setError] = useState();

    const handleScrape = async () => {
        if (!searchTerm) {
            setError("Search term is required");
            return;
        }

        setLoading(true);
        setError("");
        setResult(null);

        try {
            const response = await api.post(
                "/api/scrape_zepto",
                {
                    search_term: searchTerm,
                    pages: pages,
                },
                {
                    headers: {
                        "Content-Type": "application/json", // JSON body bhejne ke liye
                    },
                    withCredentials: false, // CORS issue avoid karne ke liye
                }
            );

            setResult(response.data);
        } catch (err) {
            console.error("Error:", err);
            setError(err.response?.data?.error || "Something went wrong");
        } finally {
            setLoading(false);
        }
    };
    return (
        <div className="flex justify-start items-center bg-gray-50 p-4">
            <Card className="w-full max-w-md shadow-lg">
                <CardBody className="space-y-4">
                    <Typography  variant="h5" color="blue-gray">
                        Zepto Scrapper
                    </Typography>

                    <Input
                        label="Search Term"
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                    />

                    <Input
                        label="Number of Pages"
                        type="number"
                        value={pages}
                        onChange={(e) => setPages(e.target.value)}
                    />

                    <Button
                        onClick={handleScrape}
                        fullWidth
                        disabled={loading}
                        className="bg-blue-600"
                    >
                        {loading ? "Scrapping..." : "Start Scrapping"}
                    </Button>

                    {error && (
                        <Typography color="red" className="text-sm">
                            {error}
                        </Typography>
                    )}

                    {result && (
                        <div>
                            <Typography>
                                ✅ Inserted: {result.inserted}
                            </Typography>
                            <Typography>
                                🔍 Scraped: {result.scraped}
                            </Typography>
                        </div>
                    )}
                </CardBody>
            </Card>
        </div>
    )
}

export default ZeptoScrapper;