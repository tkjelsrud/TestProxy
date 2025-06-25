package main

import (
	"fmt"
	"log"
	"net/http"
)

func main() {
	var err error
	routeConfig, err = LoadRoutesFromYAML("routes.yaml")
	if err != nil {
		log.Fatalf("Failed to load routes: %v", err)
	}

	http.HandleFunc("/query", HandleQuery)
	fmt.Println("Listening on :5001")
	log.Fatal(http.ListenAndServe(":5001", nil))
}
