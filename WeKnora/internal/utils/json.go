package utils

import "encoding/json"

// ToJSON converts a value to a JSON string
func ToJSON(v interface{}) string {
	json, err := json.Marshal(v)
	if err != nil {
		return ""
	}
	return string(json)
}
